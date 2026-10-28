"""The two job kinds the studio renders: FLUX 3 Klein outpainting and MiniMax H3 video.

Both start from a working copy of the picked file (``working_copy``), so EXIF orientation sets the
frame geometry and the clip orientation, and both write the result with its ``.md`` sidecar and
checkpoint into the job folder through the existing ``extend`` and ``Server.render``.
"""

from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from PIL import Image, ImageOps

from henryk_media.animation import image_to_video as i2v
from henryk_media.animation.advanced_liveportrait import COMFYUI_DIR
from henryk_media.imaging import registry
from henryk_media.imaging.composite import RESAMPLE
from henryk_media.imaging.extender import extend
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
SIZES = {"1024x768": (1024, 768), "480x320": (480, 320)}  # landscape; a portrait source swaps
WORKING_EDGE = 2048  # long edge of the working copy, as prepare_all.py scales the photos
GATE_FAILED = "no seed of 42-47 passed the person gate; the last frame is kept, marked failed"


class Generator(Protocol):
    def run(self, job: "Job", server: "StudioServer", folder: Path) -> Path:
        """Render the job into folder and return the result; its .md sidecar lies beside it."""


def working_copy(source: Path, folder: Path) -> Path:
    """Write ``<folder>/input/<stem>.png``: EXIF-upright RGB, long edge at most WORKING_EDGE."""
    with Image.open(source) as opened:
        image = ImageOps.exif_transpose(opened).convert("RGB")
    if max(image.size) > WORKING_EDGE:
        factor = WORKING_EDGE / max(image.size)
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


def video_size(source_size: tuple[int, int], resolution: str) -> tuple[int, int]:
    """Return the clip's (width, height): the preset's long side at the source's aspect.

    The short side rounds to a multiple of 32, the H3 node's step (it patchifies the latent 2x2).
    """
    long = max(SIZES[resolution])
    short = 32 * round(long * min(source_size) / max(source_size) / 32)
    return (long, short) if source_size[0] >= source_size[1] else (short, long)


class Outpaint:
    """FLUX 3 Klein over the extender recipe, with the cfg the form sets and the person gate."""

    def __init__(self, gate: PersonGate | None = None) -> None:
        self.gate = gate

    def run(self, job: "Job", server: "StudioServer", folder: Path) -> Path:
        if self.gate is None:  # loads on first use, on the CPU
            self.gate = PersonGate(COMFYUI_DIR / "models/ultralytics")
        params = job.params
        working = working_copy(Path(job.path), folder)
        base = registry.extender("flux3-klein")
        model = replace(base, settings={**base.settings, "cfg": params["cfg"]})
        output = folder / f"{working.stem}.png"
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
            width=params["width"],
        )
        if not result.gate["passed"]:
            raise RuntimeError(GATE_FAILED)
        return output


class Video:
    """MiniMax H3 at the recorded revision and settings, then FILM to 30 fps."""

    def run(self, job: "Job", server: "StudioServer", folder: Path) -> Path:
        if not i2v.FRAME_INTERPOLATION_WEIGHT.exists():  # i2v.Server.__init__ is not run
            raise FileNotFoundError(
                f"{i2v.FRAME_INTERPOLATION_WEIGHT} is missing; run make comfyui_frame_interpolation"
            )
        params = job.params
        working = working_copy(Path(job.path), folder)
        with Image.open(working) as image:
            width, height = video_size(image.size, params["resolution"])
        length, frames = DURATIONS[params["duration"]]
        clip = folder / f"{working.stem}.mp4"
        values = {
            "{{PROMPT}}": params["prompt"],
            "{{WIDTH}}": width,
            "{{HEIGHT}}": height,
            "{{LENGTH}}": length,
            "{{SEED}}": params["seed"],
        }
        server.render(working, clip, "studio", values, SETTINGS, target_frames=frames)
        return clip
