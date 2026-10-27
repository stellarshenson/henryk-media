"""Run one outpainting model over one photo and composite the result.

``extend`` fills every graph marker from the registry entry and the frame geometry, scales the
photo to the frame height and writes it into the server's input folder, runs the graph, resizes
the render to the frame size when a model's own size limit forced a smaller canvas, tone-matches
it to the photo, pastes the scaled photo back unchanged, crops the stride padding and writes the
PNG with its sidecar and checkpoint.

Every composited frame passes the no-new-people gate (``gate``). A frame whose added panels hold
a face or a person the photo does not contain is rejected and the next seed is rendered, from 42
to 47; the first clean frame is kept. If no seed passes, the last frame is kept and marked failed
in its sidecar, so the failure is visible and the tile stays out of the grids.

A graph that runs out of memory is retried at 71 percent and then 50 percent of the target size;
the largest size that fits is recorded. The photo's own pixels never enter the model's output:
every pixel at least ``feather`` inside the photo's border is bit-identical to the source.
"""

from dataclasses import asdict
from pathlib import Path

from PIL import Image

from henryk_media.animation.advanced_liveportrait import trash
from henryk_media.animation.common import project_relative
from henryk_media.imaging import composite
from henryk_media.imaging.gate import PersonGate
from henryk_media.imaging.provenance import ExtendResult, load_extend, save_extend
from henryk_media.imaging.registry import Extender
from henryk_media.imaging.server import ComfyServer, out_of_memory

ASPECTS = {"4x3": 4 / 3, "16x9": 16 / 9}  # the two frames every extender renders
FEATHER = 8  # blend band along the photo's border, in photo pixels
FALLBACK_SCALES = (1.0, 0.71, 0.5)  # render-area scales tried after an out-of-memory failure
SEEDS = 6  # seed attempts before a tile is kept and marked failed


def markers_for(
    model: Extender, geometry: composite.Geometry, render: tuple[int, int]
) -> dict[str, object]:
    """Return every graph marker for one attempt.

    Args:
        model: The extender whose settings fill the markers.
        geometry: The frame geometry.
        render: The (width, height) this attempt renders.
    """
    markers = {f"{{{{{key.upper()}}}}}": value for key, value in model.settings.items()}
    markers.update(
        {
            "{{PAD_LEFT}}": geometry.pad_left,
            "{{PAD_RIGHT}}": geometry.pad_right,
            "{{PAD_TOP}}": geometry.pad_top,
            "{{PAD_BOTTOM}}": geometry.pad_bottom,
            "{{FEATHER}}": geometry.feather,
            "{{WIDTH}}": render[0],
            "{{HEIGHT}}": render[1],
            "{{UNET}}": model.file,
        }
    )
    return markers


def attempt_frame(
    server: ComfyServer,
    model: Extender,
    photo: Image.Image,
    geometry: composite.Geometry,
    render: tuple[int, int],
    prompt: str,
    negative_prompt: str,
    seed: int,
    image_name: str,
    tag: str,
) -> tuple[Image.Image, float, int]:
    """Render one seed, tone-match it and paste the photo back.

    Args:
        server: The running ComfyUI server.
        model: The extender to run.
        photo: The photo, RGB.
        geometry: The frame geometry.
        render: The (width, height) this attempt renders.
        prompt: Positive prompt.
        negative_prompt: Negative prompt.
        seed: Graph seed for this attempt.
        image_name: File name of the photo in the server's input folder.
        tag: Filename prefix of this render, unique per attempt.

    Returns:
        The cropped composited frame, wall seconds and peak MiB.

    Raises:
        RuntimeError: If the graph fails.
    """
    markers = {
        "{{IMAGE}}": image_name,
        "{{FILENAME_PREFIX}}": tag,
        "{{PROMPT}}": prompt,
        "{{NEGATIVE_PROMPT}}": negative_prompt,
        "{{SEED}}": seed,
        **markers_for(model, geometry, render),
    }
    entry, seconds, peak_mib = server.run(server.graph(model.graph, markers))
    with Image.open(server.saved(entry)) as opened:
        frame = opened.convert("RGB")
    scaled = geometry.resized(photo)
    extended_size = geometry.extended(photo.size)
    if frame.size != extended_size:
        frame = frame.resize(extended_size, composite.RESAMPLE)
    frame = composite.tone_match(frame, scaled, geometry.origin(photo.size))
    composed = composite.paste(frame, scaled, geometry.origin(photo.size), geometry.feather)
    return composite.crop(composed, (geometry.width, geometry.height)), seconds, peak_mib


def extend(
    server: ComfyServer,
    model: Extender,
    source: Path,
    aspect: str,
    output: Path,
    prompt: str,
    negative_prompt: str,
    gate: PersonGate,
    seed: int = 42,
) -> ExtendResult:
    """Extend one photo to one landscape frame with one model.

    Args:
        server: The running ComfyUI server.
        model: The extender to run.
        source: The photo to extend.
        aspect: ``4x3`` or ``16x9``.
        output: Destination PNG; the sidecar and checkpoint are written beside it.
        prompt: Positive prompt for every model.
        negative_prompt: Negative prompt for every model.
        gate: The no-new-people gate every composited frame must pass.
        seed: First graph seed; a rejected frame advances to the next seed.

    Returns:
        The image's provenance and measurements, also saved as sidecar and checkpoint.

    Raises:
        ValueError: If the aspect is unknown.
        RuntimeError: If every size fails, or if every seed is rejected and no frame exists.
    """
    if aspect not in ASPECTS:
        raise ValueError(f"unknown aspect {aspect!r}; use one of {sorted(ASPECTS)}")
    with Image.open(source) as opened:
        photo = opened.convert("RGB")
    geometry = composite.Geometry.for_aspect(photo.size, ASPECTS[aspect], FEATHER)
    extended_size = geometry.extended(photo.size)
    photo_in_frame = geometry.photo_size(photo.size)
    settings = dict(model.settings)
    signatures = gate.signatures()
    finished = load_extend(output)
    if (
        finished is not None
        and finished.extender == model.name
        and finished.aspect == aspect
        and finished.prompt == prompt
        and finished.negative_prompt == negative_prompt
        and finished.licence == model.licence
        and finished.gate.get("start_seed") == seed
        and finished.gate.get("detectors") == signatures
        and isinstance(finished.gate.get("passed"), bool)
        and finished.geometry == asdict(geometry)
        and all(finished.settings.get(key) == value for key, value in settings.items())
    ):
        return finished

    image_name = f"{output.stem}{source.suffix}"
    rejected: list[dict[str, object]] = []
    kept: tuple[int, Image.Image, float, int, float, tuple[int, int]] | None = None
    last_verdict: dict[str, object] | None = None
    scale_index = 0
    last_error: Exception | None = None
    with server.scratch():
        geometry.resized(photo).save(server.setup.io_dirs["input"] / image_name)
        for candidate in range(seed, seed + SEEDS):
            for index in range(scale_index, len(FALLBACK_SCALES)):
                scale = FALLBACK_SCALES[index]
                render = (
                    composite.round_up(round(extended_size[0] * scale), composite.VAE_STRIDE),
                    composite.round_up(round(extended_size[1] * scale), composite.VAE_STRIDE),
                )
                try:
                    composed, seconds, peak_mib = attempt_frame(
                        server,
                        model,
                        photo,
                        geometry,
                        render,
                        prompt,
                        negative_prompt,
                        candidate,
                        image_name,
                        f"{model.name}-{aspect}-seed{candidate}",
                    )
                except RuntimeError as error:
                    if not out_of_memory(error) or scale == FALLBACK_SCALES[-1]:
                        raise
                    last_error = error
                    continue
                scale_index = index
                last_verdict = gate.check(
                    composed, geometry.origin(photo.size)[0], photo_in_frame[0]
                )
                if last_verdict["passed"]:
                    kept = (candidate, composed, seconds, peak_mib, scale, render)
                    break
                rejected.append(
                    {
                        "seed": candidate,
                        "scale": scale,
                        "violations": last_verdict["violations"],
                    }
                )
                kept = (candidate, composed, seconds, peak_mib, scale, render)
                break  # a rejected seed advances to the next seed, not to a smaller size
            if kept is not None and last_verdict and last_verdict["passed"]:
                break
        if kept is None:  # pragma: no cover - every attempt raises before this point
            raise RuntimeError(f"{model.name} failed at every size: {last_error}")

    used_seed, composed, seconds, peak_mib, scale, render = kept
    passed = bool(last_verdict and last_verdict["passed"])
    gate_record = {
        "passed": passed,
        "start_seed": seed,
        "seed": used_seed,
        "attempts": len(rejected) + (1 if passed else 0),
        "panels": last_verdict["panels"] if last_verdict else [],
        "rule": last_verdict["rule"] if last_verdict else "",
        "detectors": signatures,
        "rejected": rejected,
        "continuations": last_verdict.get("continuations", []) if last_verdict else [],
        "clipped": last_verdict.get("clipped", []) if last_verdict else [],
    }
    stale = [
        output,
        output.with_suffix(".md"),
        output.parent / "checkpoints" / f"{output.stem}.json",
    ]
    trash([path for path in stale if path.exists()])
    output.parent.mkdir(parents=True, exist_ok=True)
    composed.save(output)

    result = ExtendResult(
        image=project_relative(output),
        source=project_relative(source),
        extender=model.name,
        aspect=aspect,
        prompt=prompt,
        negative_prompt=negative_prompt,
        seed=used_seed,
        model=model.model,
        weights=model.weights,
        licence=model.licence,
        settings={**settings, "render_scale": scale},
        geometry=asdict(geometry),
        gpu=server.stats["devices"][0]["name"],
        seconds=round(seconds, 2),
        peak_vram_gb=server.peak_gb(peak_mib),
        render_width=render[0],
        render_height=render[1],
        photo_width=photo.width,
        photo_height=photo.height,
        width=composed.width,
        height=composed.height,
        ratio=round(composed.width / composed.height, 4),
        tone_matched=True,
        notes=model.notes,
        gate=gate_record,
    )
    save_extend(result, output)
    return result
