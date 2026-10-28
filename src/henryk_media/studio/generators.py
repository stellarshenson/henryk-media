"""The two job kinds the studio renders: the frame step (FLUX 3 Klein outpainting, or a crop or
scale) and MiniMax H3 video.

Both start from a working copy of the picked file (``working_copy``), so EXIF orientation sets the
frame geometry and the clip orientation, and both write the result with its ``.md`` sidecar into
the job folder; an outpaint and a clip also write a checkpoint through the existing ``extend`` and
``Server.render``.
"""

from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from PIL import Image, ImageOps

from henryk_media.animation import image_to_video as i2v
from henryk_media.animation.advanced_liveportrait import COMFYUI_DIR
from henryk_media.animation.common import project_relative
from henryk_media.imaging import registry
from henryk_media.imaging.composite import RESAMPLE, Geometry, VerticalGeometry, round_up
from henryk_media.imaging.extender import ASPECTS, FEATHER, extend
from henryk_media.imaging.gate import PersonGate

if TYPE_CHECKING:
    from henryk_media.studio.app import Job
    from henryk_media.studio.comfy import StudioServer

# tmp/workflows/image-to-video/setup-minimax.json: model and repository strings
H3_MODEL = "MiniMax H3 (FL2VA pruned bf16 transformer, 33B dense), short name minimax-h3"
H3_REVISION = "Comfy-Org/MiniMax-H3, revision e5eb578a89295337b8ff433a035929ce0279e0b6"
H3_NATIVE_FPS = 24.0
SETTINGS = {  # .agents/skills/image-to-video/references/h3-recipe.md, no negative prompt applied
    "steps": 20,
    "sampler": "res_multistep",
    "scheduler": "simple",
    "shift": "12 video, 3 audio (MiniMaxH3 model settings)",
    "cfg": "none: CFG-distilled checkpoint, BasicGuider with positive conditioning only",
    "negative_prompt": "none: the graph has no negative conditioning input",
    "weights": "minimax_h3_fl2va_pruned_bf16.safetensors, "
    "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors, minimax_h3_video_vae_fp16.safetensors, "
    "minimax_h3_audio_vae_fp32.safetensors",
}
DURATIONS = {5: (124, 150), 6: (158, 180), 10: (243, 300)}  # s: ({{LENGTH}}, frames at 30 fps)
# the frame and clip presets: short side in lines and the name; preset_size gives the long side
PRESETS = {720: "HD", 1080: "Full HD", 1440: "2K", 2160: "UHD 4K"}
H3_STEP = 32  # the H3 node needs both sides on this step (it patchifies the latent 2x2)
WORKING_EDGE = 2048  # long edge of the working copy, as prepare_all.py scales the photos;
# Outpaint raises it to the photo's long edge in a larger frame (2K, UHD 4K), up to the original
GATE_FAILED = "no seed of 42-47 passed the person gate; the last frame is kept, marked failed"
TOLERANCE = 0.01  # a photo within 1 percent of the aspect is cropped and scaled, not outpainted
LOCAL_FRAMES = ("cropped", "scaled")  # frame steps without a generative model, server or GPU


class Generator(Protocol):
    def run(self, job: "Job", server: "StudioServer | None", folder: Path) -> Path:
        """Render the job into folder and return the result; its .md sidecar lies beside it.

        ``server`` is None for a frame step that crops or scales (LOCAL_FRAMES)."""


def working_copy(source: Path, folder: Path, edge: int = WORKING_EDGE) -> Path:
    """Write ``<folder>/input/<stem>.png``: EXIF-upright RGB, long edge at most ``edge``."""
    with Image.open(source) as opened:
        image = ImageOps.exif_transpose(opened).convert("RGB")
    if max(image.size) > edge:
        factor = edge / max(image.size)
        image = image.resize((round(image.width * factor), round(image.height * factor)), RESAMPLE)
    path = folder / "input" / f"{source.stem}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    image.save(path)
    return path


def oriented_size(source: Path) -> tuple[int, int]:
    """Return (width, height) of an image after its EXIF orientation, without decoding it."""
    with Image.open(source) as image:
        width, height = image.size
        rotated = image.getexif().get(0x0112) in (5, 6, 7, 8)  # EXIF orientation tag
    return (height, width) if rotated else (width, height)


def preset_size(ratio: float, lines: int) -> tuple[int, int]:
    """Return a preset's landscape (width, height): ``lines`` high, the width ``lines * ratio``
    rounded to an even number (16:9 HD 1280x720, 4:3 HD 960x720, 3:2 HD 1080x720)."""
    return 2 * round(lines * ratio / 2), lines


def clip_size(source_size: tuple[int, int], lines: int) -> tuple[int, int]:
    """Return the clip's (width, height): the preset at the source's aspect and orientation."""
    long, short = preset_size(max(source_size) / min(source_size), lines)
    return (long, short) if source_size[0] >= source_size[1] else (short, long)


def h3_size(size: tuple[int, int]) -> tuple[int, int]:
    """Return the size H3 renders for a clip of ``size``: each side rounded up to H3_STEP."""
    return round_up(size[0], H3_STEP), round_up(size[1], H3_STEP)


def frame_step(size: tuple[int, int], aspect: str) -> str:
    """Return how the frame step brings a photo of ``size`` to ``aspect``, never stretching it.

    The step outpaints only along the larger dimension of the aspect: a narrower photo is
    outpainted sideways, a wider one is cropped sideways, and at 1:1 a landscape photo is
    outpainted above and below. A photo within TOLERANCE of the aspect is scaled.
    """
    ratio, target = size[0] / size[1], ASPECTS[aspect]
    if abs(ratio / target - 1) <= TOLERANCE:
        return "scaled"
    if ratio < target:
        return "outpainted sideways"
    return "outpainted above and below" if target == 1 else "cropped"


def window_left(photo_width: int, window: float, found: list) -> float:
    """Return the left edge of a crop ``window`` wide over the detected people.

    The window is centred on the union of every face and person box, on the largest face when
    that union is wider than the window, and on the photo when nothing is detected; it is
    clamped to the photo.

    Args:
        photo_width: Width of the photo.
        window: Width of the crop window.
        found: ``PersonGate.detections`` of the photo: detector, label, confidence, box.
    """
    boxes = [box for _, _, _, box in found]
    if not boxes:
        return (photo_width - window) / 2
    left, right = min(box[0] for box in boxes), max(box[2] for box in boxes)
    if right - left > window:
        faces = [box for detector, _, _, box in found if detector == "face"] or boxes
        left, _, right, _ = max(faces, key=lambda box: (box[2] - box[0]) * (box[3] - box[1]))
    return min(max((left + right - window) / 2, 0), photo_width - window)


class Outpaint:
    """The frame step: FLUX 3 Klein over the extender recipe, with the cfg the form sets and the
    person gate, or a crop or scale without a generative model when no outpaint is needed."""

    def __init__(self, gate: PersonGate | None = None) -> None:
        self.gate = gate

    def run(self, job: "Job", server: "StudioServer | None", folder: Path) -> Path:
        if self.gate is None:  # loads on first use, on the CPU
            self.gate = PersonGate(COMFYUI_DIR / "models/ultralytics")
        params, size = job.params, tuple(job.params["size"])
        source = oriented_size(Path(job.path))
        # the photo's long edge in the frame: a crop or scale covers it, an outpaint fits inside
        fit = max if params["frame"] in LOCAL_FRAMES else min
        need = round(max(source) * fit(size[0] / source[0], size[1] / source[1]))
        working = working_copy(Path(job.path), folder, max(WORKING_EDGE, need))
        output = folder / f"{working.stem}.png"
        with Image.open(working) as opened:
            photo = opened.convert("RGB")
        frame = Geometry.for_aspect(photo.size, ASPECTS[params["aspect"]], FEATHER, *size)
        if params["frame"] in LOCAL_FRAMES:
            return self.crop(photo, working, output, size, params)
        if params["frame"] == "outpainted above and below":
            frame = VerticalGeometry.for_size(photo.size, size, FEATHER)
        base = registry.extender("flux3-klein")
        model = replace(base, settings={**base.settings, "cfg": params["cfg"]})
        result = extend(
            server,
            model,
            working,
            params["aspect"],
            output,
            params["prompt"],
            params["negative_prompt"],
            self.gate,
            seed=42,
            geometry=frame,
        )
        sidecar = output.with_suffix(".md")
        sidecar.write_text(f"Frame step: {params['frame']}\n\n{sidecar.read_text()}")
        if not result.gate["passed"]:
            raise RuntimeError(GATE_FAILED)
        return output

    def crop(
        self, photo: Image.Image, working: Path, output: Path, size: tuple[int, int], params: dict
    ) -> Path:
        """Crop the photo to the frame's aspect and scale it with Lanczos; no generative model."""
        aspect = params["aspect"].replace("x", ":")
        lines = [f"- Source working copy: `{project_relative(working)}`"]
        if params["frame"] == "scaled":
            step = f"scaled, the photo already had the {aspect} aspect, no generative model"
            ImageOps.fit(photo, size, RESAMPLE).save(output)
            lines.append(f"- Crop window: centred, the sliver beyond {size[0]}:{size[1]}")
        else:
            found = self.gate.detections(photo)
            window = photo.height * size[0] / size[1]
            left = window_left(photo.width, window, found)
            placed = "over the detected people" if found else "centred, no person detected"
            step = (
                f"cropped sideways from {photo.width}x{photo.height} {placed}, no generative model"
            )
            photo.resize(size, RESAMPLE, box=(left, 0, left + window, photo.height)).save(output)
            lines += [
                "- Detections: "
                + (
                    "; ".join(
                        f"{detector} {confidence:.2f} box ({x1:.0f},{y1:.0f},{x2:.0f},{y2:.0f})"
                        for detector, _, confidence, (x1, y1, x2, y2) in found
                    )
                    or "none"
                ),
                f"- Crop window: x {left:.0f}-{left + window:.0f} of {photo.width} px",
            ]
        lines += ["- Resampling: Lanczos", f"- Output: {size[0]} x {size[1]} px"]
        output.with_suffix(".md").write_text(
            f"Frame step: {step}\n\n# {output.name}\n\n" + "\n".join(lines) + "\n"
        )
        return output


class Video:
    """MiniMax H3 at the recorded revision and settings, then FILM to 30 fps.

    H3 stretches its input onto a canvas whose sides are multiples of H3_STEP, so it renders at
    the clip size rounded up to that step from the input scaled to cover the render size and
    centre-cropped to it, and the graph centre-crops the decoded frames to the exact clip size:
    the clip has the preset size at the input's aspect and nothing is stretched.
    """

    def run(self, job: "Job", server: "StudioServer", folder: Path) -> Path:
        if not i2v.FRAME_INTERPOLATION_WEIGHT.exists():  # i2v.Server.__init__ is not run
            raise FileNotFoundError(
                f"{i2v.FRAME_INTERPOLATION_WEIGHT} is missing; run make comfyui_frame_interpolation"
            )
        params = job.params
        (width, height), render = params["size"], params["render"]
        working = working_copy(Path(job.path), folder, max(WORKING_EDGE, max(render)))
        with Image.open(working) as image:
            fed = ImageOps.fit(image, tuple(render), RESAMPLE)  # cover, centre crop, no stretch
        fed.save(working)  # the copy H3 receives
        length, frames = DURATIONS[params["duration"]]
        clip = folder / f"{working.stem}.mp4"
        values = {
            "{{PROMPT}}": params["prompt"],
            "{{WIDTH}}": render[0],
            "{{HEIGHT}}": render[1],
            "{{CROP_WIDTH}}": width,
            "{{CROP_HEIGHT}}": height,
            "{{CROP_X}}": (render[0] - width) // 2,
            "{{CROP_Y}}": (render[1] - height) // 2,
            "{{LENGTH}}": length,
            "{{SEED}}": params["seed"],
        }
        server.render(working, clip, "studio", values, SETTINGS, target_frames=frames)
        return clip
