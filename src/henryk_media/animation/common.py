"""Helpers every photo-animation notebook shares.

A model module renders one working copy into one clip. This module names the clip files, measures
the render, reads the written clip back, and saves the clip's Markdown sidecar together with a JSON
checkpoint, so a re-run restores finished clips instead of rendering them again.
"""

from collections.abc import Callable
from dataclasses import asdict, dataclass
import io
import json
import os
from pathlib import Path
import random
import time

import cv2
import numpy as np
from PIL import Image, ImageCms
import torch

from henryk_media.config import PROCESSED_DATA_DIR, PROJ_ROOT

BYTES_PER_GB = 1e9

Box = tuple[int, int, int, int]  # x0, y0, x1, y1 in image pixels


@dataclass
class ClipResult:
    """Provenance and measurements of one rendered clip; paths are relative to the project root."""

    clip: str
    source: str
    driving: str
    model: str
    revision: str
    variant: str
    settings: dict[str, object]
    gpu: str
    seconds: float
    peak_vram_gb: float
    width: int
    height: int
    frames: int
    fps: float
    time_scope: str = "render call only, model loading excluded"
    vram_scope: str = "PyTorch allocations"


def set_seed(seed: int) -> None:
    """Seed Python, NumPy and PyTorch random generators."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def load_working_copy(path: Path) -> np.ndarray:
    """Return a working copy as an RGB uint8 array of shape (height, width, 3)."""
    with Image.open(path) as image:
        return np.asarray(image.convert("RGB"))


def colour_profile(path: Path) -> str | None:
    """Return the description of the image's embedded ICC profile, or None when it has none."""
    with Image.open(path) as image:
        icc = image.info.get("icc_profile")
    if not icc:
        return None
    return ImageCms.getProfileDescription(ImageCms.ImageCmsProfile(io.BytesIO(icc))).strip()


def project_relative(path: Path) -> str:
    """Return the path relative to the project root, as stored in sidecars and checkpoints."""
    return str(path.resolve().relative_to(PROJ_ROOT))


def output_dir(photo_set: str, model: str) -> Path:
    """Return ``data/processed/<photo_set>/<model>``, the folder of one model's clips."""
    return PROCESSED_DATA_DIR / photo_set / model


def clip_path(output: Path, source: Path, variant: str) -> Path:
    """Return ``<output>/<source stem>--<variant>.mp4``."""
    return output / f"{source.stem}--{variant}.mp4"


def checkpoint_path(clip: Path) -> Path:
    """Return the clip's JSON checkpoint: ``checkpoints/<clip stem>.json`` beside the clip."""
    return clip.parent / "checkpoints" / f"{clip.stem}.json"


def measure[T](render: Callable[[], T]) -> tuple[T, float, float]:
    """Run one render and return (its result, wall seconds, peak PyTorch VRAM in GB).

    The peak counts PyTorch allocations only; memory held by other runtimes such as
    onnxruntime is not included.
    """
    torch.cuda.synchronize()
    torch.cuda.reset_peak_memory_stats()
    start = time.perf_counter()
    result = render()
    torch.cuda.synchronize()
    seconds = time.perf_counter() - start
    return result, seconds, torch.cuda.max_memory_allocated() / BYTES_PER_GB


def probe_clip(clip: Path) -> tuple[int, int, int, float]:
    """Return (width, height, frame count, fps) of a video file.

    Raises:
        FileNotFoundError: If OpenCV cannot open the file.
    """
    capture = cv2.VideoCapture(str(clip))
    if not capture.isOpened():
        raise FileNotFoundError(f"cannot open video: {clip}")
    try:
        return (
            int(capture.get(cv2.CAP_PROP_FRAME_WIDTH)),
            int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)),
            int(capture.get(cv2.CAP_PROP_FRAME_COUNT)),
            capture.get(cv2.CAP_PROP_FPS),
        )
    finally:
        capture.release()


def region_motion(clip: Path, boxes: list[Box]) -> list[float]:
    """Return, per box, the mean absolute pixel change against frame 0 over all later frames.

    Values are on the 0-255 scale; 0 means the region never changed.

    Raises:
        FileNotFoundError: If OpenCV cannot open the file.
    """
    capture = cv2.VideoCapture(str(clip))
    if not capture.isOpened():
        raise FileNotFoundError(f"cannot open video: {clip}")
    ok, first = capture.read()
    totals, frames = np.zeros(len(boxes)), 0
    while ok:
        ok, frame = capture.read()
        if not ok:
            break
        change = cv2.absdiff(frame, first)
        totals += [change[y0:y1, x0:x1].mean() for x0, y0, x1, y1 in boxes]
        frames += 1
    capture.release()
    return (totals / max(frames, 1)).tolist()


def changed_region(clip: Path, threshold: float) -> Box | None:
    """Return the bounding box of the pixels that change by more than threshold against frame 0.

    A pixel's change is its largest absolute difference against frame 0 over all frames, averaged
    over the colour channels, on the 0-255 scale. A 5 x 5 opening removes isolated pixels, so
    single codec-noise spikes do not widen the box.

    Returns:
        (x0, y0, x1, y1) in clip pixels, or None when no pixel changes by more than threshold.

    Raises:
        FileNotFoundError: If OpenCV cannot open the file.
    """
    capture = cv2.VideoCapture(str(clip))
    if not capture.isOpened():
        raise FileNotFoundError(f"cannot open video: {clip}")
    ok, first = capture.read()
    largest = np.zeros(first.shape[:2], np.float32)
    while ok:
        ok, frame = capture.read()
        if ok:
            np.maximum(largest, cv2.absdiff(frame, first).mean(axis=2), out=largest)
    capture.release()
    mask = cv2.morphologyEx(
        (largest > threshold).astype(np.uint8), cv2.MORPH_OPEN, np.ones((5, 5))
    )
    points = cv2.findNonZero(mask)
    if points is None:
        return None
    x, y, width, height = cv2.boundingRect(points)
    return x, y, x + width, y + height


def sidecar_text(result: ClipResult) -> str:
    """Return the Markdown sidecar describing one clip; the driving line only when there is one."""
    settings = ", ".join(f"`{key}={value}`" for key, value in result.settings.items())
    driving = f"- Driving clip: `{result.driving}`\n" if result.driving else ""
    return (
        f"# {Path(result.clip).name}\n\n"
        f"- Source working copy: `{result.source}`\n"
        f"- Model: {result.model}, {result.revision}\n"
        f"{driving}"
        f"- Variant: `{result.variant}`\n"
        f"- Settings: {settings}\n"
        f"- Output: {result.width} x {result.height} px, {result.frames} frames at "
        f"{result.fps:g} fps ({result.frames / result.fps:.2f} s)\n"
        f"- GPU: {result.gpu}\n"
        f"- Render time: {result.seconds:.1f} s ({result.time_scope})\n"
        f"- Peak VRAM: {result.peak_vram_gb:.2f} GB ({result.vram_scope})\n"
    )


def save_result(result: ClipResult, clip: Path) -> None:
    """Write the clip's Markdown sidecar and its JSON checkpoint beside the clip."""
    clip.with_suffix(".md").write_text(sidecar_text(result))
    checkpoint = checkpoint_path(clip)
    checkpoint.parent.mkdir(parents=True, exist_ok=True)
    staged = checkpoint.with_name(checkpoint.name + ".tmp")
    staged.write_text(json.dumps(asdict(result), indent=2))
    os.replace(staged, checkpoint)


def load_result(clip: Path) -> ClipResult | None:
    """Return the saved result of a finished clip, or None when the clip or checkpoint is missing.

    A checkpoint that is not valid UTF-8 JSON or not a ClipResult is also None, so the clip is
    rendered again instead of raising.
    """
    checkpoint = checkpoint_path(clip)
    if not (clip.exists() and checkpoint.exists()):
        return None
    try:
        return ClipResult(**json.loads(checkpoint.read_text()))
    except (json.JSONDecodeError, TypeError, UnicodeDecodeError):
        return None
