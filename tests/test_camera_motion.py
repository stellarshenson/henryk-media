"""Tests for the camera-motion measurement."""

from pathlib import Path

import cv2
import numpy as np
import pytest

from henryk_media.animation.camera_motion import frame_motion

SIZE = (320, 240)  # width, height of the test clips


def write_clip(path: Path, shift: float, frames: int = 21) -> None:
    """Write a clip of a textured field that moves ``shift`` pixels right per frame."""
    field = cv2.GaussianBlur(
        np.random.default_rng(0).integers(0, 256, (400, 400), np.uint8), (3, 3), 0
    )
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 30, SIZE)
    for index in range(frames):
        matrix = np.float32([[1, 0, shift * index], [0, 1, 0]])
        frame = cv2.warpAffine(field, matrix, SIZE, borderMode=cv2.BORDER_REFLECT)
        writer.write(cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR))
    writer.release()


def test_moving_background_reads_as_translation(tmp_path: Path) -> None:
    clip = tmp_path / "moving.mp4"
    write_clip(clip, shift=0.5)  # 2.5 px per sampled pair, 10 px over the clip
    motion = frame_motion(clip, step=5)
    assert motion.frames == 21 and len(motion.steps) == 4 and motion.failed_steps == 0
    assert motion.cumulative_translation_px_max == pytest.approx(10.0, abs=1.0)
    assert motion.scale_min == pytest.approx(1.0, abs=0.005)
    assert motion.rotation_deg_max < 0.5
    assert motion.steps[-1].tx == pytest.approx(10.0, abs=1.0)
    assert motion.steps[-1].ty == pytest.approx(0.0, abs=1.0)


def test_still_background_reads_as_no_motion(tmp_path: Path) -> None:
    clip = tmp_path / "still.mp4"
    write_clip(clip, shift=0.0)
    motion = frame_motion(clip, step=5)
    assert motion.cumulative_translation_px_max < 0.5
    assert motion.scale_min == pytest.approx(1.0, abs=0.005)
    assert motion.rotation_deg_max < 0.2
