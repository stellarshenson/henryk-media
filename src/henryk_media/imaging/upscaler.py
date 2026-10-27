"""Run one upscaling model over one extended frame and composite the photo back.

``upscale`` loads the frame's extension checkpoint, sizes the upscaler's input so its own factor
lands on twice the extended size (or the largest size that fits after an out-of-memory failure),
runs the graph, tone-matches the result to the photo at the output scale, pastes the photo back,
and writes the PNG with a sidecar naming both models.

Every upscaled tile passes the no-new-people gate as well: a generative upscaler can add a face
to a side panel even when the extender's frame was clean. A rejected tile is re-rendered with the
next seed, 42 to 47; the first clean tile is kept, and a tile that never passes is marked failed
and stays out of the grids.

The photo is resampled once, to the output height. The upscaler's detail gain applies to the two
new side panels and the seam; the child's own pixels are never regenerated.
"""

from pathlib import Path

from PIL import Image

from henryk_media.animation.advanced_liveportrait import trash
from henryk_media.animation.common import project_relative
from henryk_media.imaging import composite
from henryk_media.imaging.gate import PersonGate
from henryk_media.imaging.provenance import UpscaleResult, load_extend, load_upscale, save_upscale
from henryk_media.imaging.registry import Upscaler
from henryk_media.imaging.server import ComfyServer, out_of_memory

FALLBACK_SCALES = (1.0, 0.71, 0.5)  # render-area scales tried after an out-of-memory failure
SEEDS = 6  # seed attempts before a tile is kept and marked failed


def upscale(
    server: ComfyServer,
    model: Upscaler,
    source: Path,
    output: Path,
    gate: PersonGate,
    seed: int = 42,
    factor: float = 2.0,
) -> UpscaleResult:
    """Upscale one extended frame with one model.

    Args:
        server: The running ComfyUI server.
        model: The upscaler to run.
        source: The extended PNG; its checkpoint names the extender.
        output: Destination PNG; the sidecar and checkpoint are written beside it.
        gate: The no-new-people gate every composited tile must pass.
        seed: First graph seed; a rejected tile advances to the next seed.
        factor: Target size as a multiple of the extended frame.

    Returns:
        The image's provenance and measurements, including the extender's record.

    Raises:
        ValueError: If the source has no extension checkpoint.
        RuntimeError: If every attempt fails.
    """
    extension = load_extend(source)
    if extension is None:
        raise ValueError(f"{source} has no extension checkpoint; run the extender first")
    geometry = composite.Geometry(**extension.geometry)
    extended = (extension.width, extension.height)
    target = composite.target_size(extended, factor)
    photo_size = geometry.photo_size((extension.photo_width, extension.photo_height))
    settings = {
        **model.settings,
        "target": list(target),
        "prompt": model.prompt,
        "factor": factor,
    }
    signatures = gate.signatures()
    finished = load_upscale(output)
    if (
        finished is not None
        and finished.upscaler == model.name
        and finished.prompt == model.prompt
        and finished.gate.get("start_seed") == seed
        and finished.gate.get("detectors") == signatures
        and isinstance(finished.gate.get("passed"), bool)
        and all(finished.settings.get(key) == value for key, value in settings.items())
    ):
        return finished

    image_name = f"{output.stem}-input{source.suffix}"
    photo_width = round(photo_size[0] * target[0] / extended[0])
    origin = (round(geometry.pad_left * target[0] / extended[0]), 0)
    feather = max(1, round(geometry.feather * target[0] / extended[0]))
    with Image.open(source) as opened:
        photo = opened.convert("RGB").crop(
            (geometry.pad_left, 0, geometry.pad_left + photo_size[0], photo_size[1])
        )
    photo = photo.resize((photo_width, target[1]), composite.RESAMPLE)

    rejected: list[dict[str, object]] = []
    kept: tuple[int, Image.Image, float, int, float, tuple[int, int]] | None = None
    last_verdict: dict[str, object] | None = None
    scale_index = 0
    last_error: Exception | None = None
    with server.scratch():
        for candidate in range(seed, seed + SEEDS):
            for index in range(scale_index, len(FALLBACK_SCALES)):
                scale = FALLBACK_SCALES[index]
                render = tuple(
                    composite.round_up(round(side * scale), composite.VAE_STRIDE)
                    for side in composite.render_size(target)
                )
                input_size = (
                    max(1, round(render[0] / model.scale)),
                    max(1, round(render[1] / model.scale)),
                )
                with Image.open(source) as opened:
                    opened.convert("RGB").resize(input_size, composite.RESAMPLE).save(
                        server.setup.io_dirs["input"] / image_name
                    )
                markers = {
                    f"{{{{{key.upper()}}}}}": value for key, value in model.settings.items()
                }
                markers.update(
                    {
                        "{{IMAGE}}": image_name,
                        "{{FILENAME_PREFIX}}": f"{model.name}-seed{candidate}",
                        "{{SEED}}": candidate,
                        "{{WIDTH}}": render[0],
                        "{{HEIGHT}}": render[1],
                        "{{MODEL}}": model.file,
                        "{{SCALE}}": model.scale,
                        "{{PROMPT}}": model.prompt,
                        "{{NEGATIVE_PROMPT}}": (
                            "blurry, low quality, distorted, deformed, text, watermark"
                        ),
                        "{{BASE_MODEL}}": server.setup.paths.get("hypir_base_model", ""),
                    }
                )
                try:
                    entry, seconds, peak_mib = server.run(server.graph(model.graph, markers))
                except RuntimeError as error:
                    if not out_of_memory(error) or scale == FALLBACK_SCALES[-1]:
                        raise
                    last_error = error
                    continue
                scale_index = index
                with Image.open(server.saved(entry)) as opened:
                    frame = opened.convert("RGB")
                if frame.size != target:
                    frame = frame.resize(target, composite.RESAMPLE)
                frame = composite.tone_match(frame, photo, origin)
                composed = composite.paste(frame, photo, origin, feather)
                last_verdict = gate.check(composed, origin[0], photo_width)
                kept = (candidate, composed, seconds, peak_mib, scale, render)
                if last_verdict["passed"]:
                    break
                rejected.append(
                    {
                        "seed": candidate,
                        "scale": scale,
                        "violations": last_verdict["violations"],
                    }
                )
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
    output.parent.mkdir(parents=True, exist_ok=True)
    stale = [
        output,
        output.with_suffix(".md"),
        output.parent / "checkpoints" / f"{output.stem}.json",
    ]
    trash([path for path in stale if path.exists()])
    composed.save(output)

    result = UpscaleResult(
        image=project_relative(output),
        source=project_relative(source),
        upscaler=model.name,
        model=model.model,
        weights=model.weights,
        licence=model.licence,
        prompt=model.prompt,
        seed=used_seed,
        settings={**settings, "render": list(render)},
        target_width=target[0],
        target_height=target[1],
        render_width=render[0],
        render_height=render[1],
        width=composed.width,
        height=composed.height,
        ratio=round(composed.width / composed.height, 4),
        extender=extension,
        gpu=server.stats["devices"][0]["name"],
        seconds=round(seconds, 2),
        peak_vram_gb=server.peak_gb(peak_mib),
        notes=model.notes,
        gate=gate_record,
    )
    save_upscale(result, output)
    return result
