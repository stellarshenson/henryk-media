"""Provenance of one bench image: the Markdown sidecar and the JSON checkpoint.

A sidecar names the source, the model and its weights and licence, the prompt, the negative
prompt, the seed, the settings, the size, the render time and the peak VRAM, so no generated
image can be mistaken for a genuine recording. A combined sidecar names the extender and the
upscaler both. The checkpoint holds the same records plus the measurements, and a rerun restores
a finished image whose checkpoint equals the requested render instead of rendering it again.
"""

from dataclasses import asdict, dataclass, field
import json
from pathlib import Path

from henryk_media.imaging.gate import detection_text


@dataclass
class ExtendResult:
    """Provenance and measurements of one extension; paths are relative to the project root.

    Attributes:
        image: Output image path.
        source: Photo the frame was extended from.
        extender: Registry name of the outpainting model.
        aspect: ``4x3`` or ``16x9``.
        prompt: Positive prompt submitted to the graph.
        negative_prompt: Negative prompt submitted to the graph.
        seed: Graph seed.
        model: Human description of the model.
        weights: Repositories and files the model was loaded from.
        licence: Licence of the model and its weights.
        settings: Graph marker values and the frame geometry.
        geometry: Pads and feather of the frame, as the extender recorded them.
        gpu: GPU name the server reported.
        seconds: Wall seconds from submission to the finished history entry.
        peak_vram_gb: Highest GPU memory above the idle baseline.
        render_width: Width the graph rendered.
        render_height: Height the graph rendered.
        photo_width: Width of the source photo, before the scale to the frame height.
        photo_height: Height of the source photo, which sets the frame height.
        width: Width of the saved frame.
        height: Height of the saved frame.
        ratio: Saved width / height.
        tone_matched: Whether the rendered frame was tone-matched before the paste-back.
        notes: Model limits recorded with the image.
        gate: No-new-people verdict, detectors and every rejected seed with its boxes.
    """

    image: str
    source: str
    extender: str
    aspect: str
    prompt: str
    negative_prompt: str
    seed: int
    model: str
    weights: str
    licence: str
    settings: dict[str, object]
    geometry: dict[str, int]
    gpu: str
    seconds: float
    peak_vram_gb: float
    render_width: int
    render_height: int
    photo_width: int
    photo_height: int
    width: int
    height: int
    ratio: float
    tone_matched: bool
    notes: str = ""
    gate: dict[str, object] = field(default_factory=dict)
    time_scope: str = "POST /prompt to the finished history entry"
    vram_scope: str = (
        "nvidia-smi memory.used of the pinned GPU sampled during the render, minus the memory in "
        "use before the server started"
    )


@dataclass
class UpscaleResult:
    """Provenance and measurements of one upscaled image and the extension it came from.

    Attributes:
        image: Output image path.
        source: Extended image the upscaler ran on.
        upscaler: Registry name of the upscaler.
        model: Human description of the upscaler.
        weights: Repositories and files the upscaler was loaded from.
        licence: Licence of the upscaler.
        prompt: Prompt the upscaler was given, empty when it takes none.
        seed: Graph seed.
        settings: Graph marker values.
        target_width: Requested output width, twice the extended width.
        target_height: Requested output height.
        render_width: Width the graph rendered, a multiple of the VAE stride.
        render_height: Height the graph rendered.
        width: Width of the saved image.
        height: Height of the saved image.
        ratio: Saved width / height.
        extender: Provenance of the extension the image came from.
        gpu: GPU name the server reported.
        seconds: Wall seconds from submission to the finished history entry.
        peak_vram_gb: Highest GPU memory above the idle baseline.
        notes: Model limits recorded with the image.
        gate: No-new-people verdict of the upscaled tile, with its rejected seeds and boxes.
    """

    image: str
    source: str
    upscaler: str
    model: str
    weights: str
    licence: str
    prompt: str
    seed: int
    settings: dict[str, object]
    target_width: int
    target_height: int
    render_width: int
    render_height: int
    width: int
    height: int
    ratio: float
    extender: ExtendResult
    gpu: str
    seconds: float
    peak_vram_gb: float
    notes: str = ""
    gate: dict[str, object] = field(default_factory=dict)
    time_scope: str = "POST /prompt to the finished history entry"
    vram_scope: str = (
        "nvidia-smi memory.used of the pinned GPU sampled during the render, minus the memory in "
        "use before the server started"
    )


def checkpoint_path(image: Path) -> Path:
    """Return the image's JSON checkpoint: ``checkpoints/<image stem>.json`` beside the image."""
    return image.parent / "checkpoints" / f"{image.stem}.json"


def _settings_lines(settings: dict[str, object]) -> str:
    """Return the settings as one Markdown line of ``key=value`` pairs."""
    return ", ".join(f"`{key}={value}`" for key, value in settings.items())


def kept_strangers(gate: dict[str, object]) -> list[dict[str, object]]:
    """Return the strangers detected in the kept tile.

    A passing record has none by definition. A failing record keeps them in the last entry of
    ``rejected``, the attempt whose frame was kept; a re-scored record may also carry a top-level
    ``strangers`` list.

    Args:
        gate: The gate record of an extended or upscaled image.
    """
    strangers = gate.get("strangers")
    if strangers is not None:
        return strangers
    if gate.get("passed"):
        return []
    rejected = gate.get("rejected") or []
    return rejected[-1].get("violations", []) if rejected else []


def _detection_line(name: str, items: list[dict[str, object]]) -> str:
    """Return one sidecar line listing detections, with their count and boxes."""
    if not items:
        return f"- {name}: none"
    noun = "box" if len(items) == 1 else "boxes"
    return f"- {name} ({len(items)} {noun}): " + "; ".join(detection_text(item) for item in items)


def gate_lines(gate: dict[str, object], label: str = "Gate") -> str:
    """Return the gate's sidecar lines: verdict, detectors, rule and every detection kind.

    Args:
        gate: The gate record of an extended or upscaled image.
        label: Name the lines carry, so a combined sidecar can tell its two gates apart.
    """
    if not gate:
        return f"- {label}: not recorded\n"
    detectors = gate.get("detectors") or {}
    detector_text = "; ".join(f"{name} {value}" for name, value in detectors.items())
    panels = gate.get("panels") or []
    axis = gate.get("axis", "x")  # y for panels above and below the photo
    panel_text = " and ".join(f"{axis} {left}-{right}" for left, right in panels)
    strangers = kept_strangers(gate)
    continuations = gate.get("continuations") or []
    clipped = gate.get("clipped") or []
    verdict = "passed" if gate.get("passed") else "FAILED"
    return (
        f"- {label}: {verdict}; kept seed {gate.get('seed')}; strangers {len(strangers)}; "
        f"continuations {len(continuations)}; clipped {len(clipped)}; panels {panel_text}\n"
        f"- {label} detectors: {detector_text}; rule: {gate.get('rule', '')}\n"
        f"{_detection_line(f'{label} strangers', strangers)}\n"
        f"{_detection_line(f'{label} continuations', continuations)}\n"
        f"{_detection_line(f'{label} clipped', clipped)}\n"
    )


def extend_sidecar(result: ExtendResult) -> str:
    """Return the Markdown sidecar describing one extended image."""
    return (
        f"# {Path(result.image).name}\n\n"
        f"- Source working copy: `{result.source}`\n"
        f"- Extender: {result.model}\n"
        f"- Extender weights: {result.weights}\n"
        f"- Extender licence: {result.licence}\n"
        f"- Prompt: {result.prompt}\n"
        f"- Negative prompt: {result.negative_prompt or '(empty)'}\n"
        f"- Seed: {result.seed}\n"
        f"{gate_lines(result.gate)}"
        f"- Settings: {_settings_lines(result.settings)}\n"
        f"- Frame: pads left {result.geometry['pad_left']}, right {result.geometry['pad_right']}, "
        f"top {result.geometry['pad_top']}, bottom {result.geometry['pad_bottom']}, "
        f"feather {result.geometry['feather']} px\n"
        f"- Tone match: {'per-channel mean and standard deviation over the photo region' if result.tone_matched else 'none'}\n"
        f"- Render: {result.render_width} x {result.render_height} px, "
        f"cropped to {result.width} x {result.height} px\n"
        f"- Output: {result.width} x {result.height} px, ratio {result.ratio:.4f}\n"
        f"- GPU: {result.gpu}\n"
        f"- Render time: {result.seconds:.1f} s ({result.time_scope})\n"
        f"- Peak VRAM: {result.peak_vram_gb:.2f} GB ({result.vram_scope})\n"
        + (f"- Notes: {result.notes}\n" if result.notes else "")
    )


def combined_sidecar(result: UpscaleResult) -> str:
    """Return the Markdown sidecar describing one extended and upscaled image."""
    extended = result.extender
    return (
        f"# {Path(result.image).name}\n\n"
        f"- Source working copy: `{extended.source}`\n"
        f"- Extender: {extended.model} ({extended.extender}, {extended.aspect})\n"
        f"- Extender weights: {extended.weights}\n"
        f"- Extender licence: {extended.licence}\n"
        f"- Extender prompt: {extended.prompt}\n"
        f"- Extender negative prompt: {extended.negative_prompt or '(empty)'}\n"
        f"- Extender seed: {extended.seed}\n"
        f"{gate_lines(extended.gate, 'Extender gate')}"
        f"- Extender settings: {_settings_lines(extended.settings)}\n"
        f"- Extender render: {extended.width} x {extended.height} px, "
        f"{extended.seconds:.1f} s, peak {extended.peak_vram_gb:.2f} GB\n"
        f"- Upscaler: {result.model}\n"
        f"- Upscaler weights: {result.weights}\n"
        f"- Upscaler licence: {result.licence}\n"
        f"- Upscaler prompt: {result.prompt or '(none)'}\n"
        f"- Upscaler settings: {_settings_lines(result.settings)}\n"
        f"{gate_lines(result.gate, 'Upscaler gate')}"
        f"- Target size: {result.target_width} x {result.target_height} px\n"
        f"- Render: {result.render_width} x {result.render_height} px, "
        f"cropped to {result.width} x {result.height} px\n"
        f"- Output: {result.width} x {result.height} px, ratio {result.ratio:.4f}\n"
        f"- Composite: the photo pasted back, resampled once, after a per-channel tone match\n"
        f"- GPU: {result.gpu}\n"
        f"- Render time: {result.seconds:.1f} s ({result.time_scope})\n"
        f"- Peak VRAM: {result.peak_vram_gb:.2f} GB ({result.vram_scope})\n"
        + (f"- Notes: {result.notes}\n" if result.notes else "")
    )


def save_extend(result: ExtendResult, image: Path) -> None:
    """Write an extended image's Markdown sidecar and JSON checkpoint beside the image."""
    image.with_suffix(".md").write_text(extend_sidecar(result))
    checkpoint = checkpoint_path(image)
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    checkpoint.write_text(json.dumps(asdict(result), indent=2))


def save_upscale(result: UpscaleResult, image: Path) -> None:
    """Write a combined image's Markdown sidecar and JSON checkpoint beside the image."""
    image.with_suffix(".md").write_text(combined_sidecar(result))
    checkpoint = checkpoint_path(image)
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    checkpoint.write_text(json.dumps(asdict(result), indent=2))


def load_extend(image: Path) -> ExtendResult | None:
    """Return the saved extension of a finished image, or None when either file is missing."""
    checkpoint = checkpoint_path(image)
    if not (image.exists() and checkpoint.exists()):
        return None
    return ExtendResult(**json.loads(checkpoint.read_text()))


def load_upscale(image: Path) -> UpscaleResult | None:
    """Return the saved upscale of a finished image, or None when either file is missing."""
    checkpoint = checkpoint_path(image)
    if not (image.exists() and checkpoint.exists()):
        return None
    data = json.loads(checkpoint.read_text())
    data["extender"] = ExtendResult(**data["extender"])
    return UpscaleResult(**data)
