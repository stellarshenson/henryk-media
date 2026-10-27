"""Camera-motion measurement for rendered clips.

A whole-frame image-to-video model redraws the photo and can move the camera even though the
source is a still. This module measures that motion from the clip itself: SIFT features in the
outer band of the frame, where the background sits, a RANSAC similarity transform between two
sampled frames, and the composed path relative to frame 0. A still camera leaves the background
band in place, so every number is near zero.
"""

from dataclasses import dataclass
from pathlib import Path
from statistics import median

import cv2
import numpy as np

BORDER_FRACTION = 0.10  # outer band of the frame used as background evidence
STEP = 5  # frames between sampled pairs
MIN_INLIERS = 8  # matches a similarity fit needs before it is trusted
RATIO = 0.75  # Lowe ratio for SIFT matches

Box = tuple[int, int, int, int]  # x0, y0, x1, y1


@dataclass(frozen=True)
class CameraStep:
    """Background transform relative to frame 0 at one sampled frame.

    Attributes:
        frame: Frame index the transform maps frame 0 content onto.
        inliers: RANSAC inliers of the last pair in the chain.
        scale: Cumulative scale, 1.0 for no zoom.
        rotation_deg: Cumulative rotation in degrees.
        tx: Cumulative horizontal translation in pixels.
        ty: Cumulative vertical translation in pixels.
    """

    frame: int
    inliers: int
    scale: float
    rotation_deg: float
    tx: float
    ty: float


@dataclass(frozen=True)
class CameraMotion:
    """Background motion of one clip, chained over sampled frame pairs.

    Attributes:
        frames: Frame count of the clip.
        step: Frames between sampled pairs.
        steps: One record per fitted pair.
        failed_steps: Pairs with too few matches to fit; each one hides motion.
        step_translation_px_median: Median background translation per sampled pair.
        step_translation_px_max: Largest background translation per sampled pair.
        cumulative_translation_px_max: Largest displacement from frame 0 over the clip.
        scale_min: Smallest cumulative scale.
        scale_max: Largest cumulative scale.
        rotation_deg_max: Largest absolute cumulative rotation.
        inliers_median: Median RANSAC inliers per fitted pair.
    """

    frames: int
    step: int
    steps: tuple[CameraStep, ...]
    failed_steps: int
    step_translation_px_median: float
    step_translation_px_max: float
    cumulative_translation_px_max: float
    scale_min: float
    scale_max: float
    rotation_deg_max: float
    inliers_median: float


def border_mask(shape: tuple[int, int], fraction: float = BORDER_FRACTION) -> np.ndarray:
    """Return a uint8 mask of the frame's outer band, where the background is measured."""
    height, width = shape
    mask = np.zeros((height, width), np.uint8)
    band_x, band_y = max(1, int(width * fraction)), max(1, int(height * fraction))
    mask[:band_y, :] = 255
    mask[-band_y:, :] = 255
    mask[:, :band_x] = 255
    mask[:, -band_x:] = 255
    return mask


def pair_transform(
    source: np.ndarray, target: np.ndarray, mask: np.ndarray, sift: cv2.SIFT
) -> tuple[np.ndarray | None, int]:
    """Return the RANSAC similarity from ``source`` to ``target`` inside ``mask`` and its inliers.

    Returns:
        ((3, 3) float32 transform, inlier count); ``(None, 0)`` when too few matches fit.
    """
    keypoints_a, descriptors_a = sift.detectAndCompute(source, mask)
    keypoints_b, descriptors_b = sift.detectAndCompute(target, mask)
    if descriptors_a is None or descriptors_b is None:
        return None, 0
    pairs = cv2.BFMatcher().knnMatch(descriptors_a, descriptors_b, k=2)
    good = [match for match, runner_up in pairs if match.distance < RATIO * runner_up.distance]
    if len(good) < MIN_INLIERS:
        return None, len(good)
    points_a = np.float32([keypoints_a[m.queryIdx].pt for m in good]).reshape(-1, 1, 2)
    points_b = np.float32([keypoints_b[m.trainIdx].pt for m in good]).reshape(-1, 1, 2)
    matrix, inliers = cv2.estimateAffinePartial2D(
        points_a, points_b, method=cv2.RANSAC, ransacReprojThreshold=3.0
    )
    if matrix is None or inliers is None or int(inliers.sum()) < MIN_INLIERS:
        return None, 0
    return np.vstack([matrix, [0.0, 0.0, 1.0]]).astype(np.float32), int(inliers.sum())


def frame_motion(clip: Path, step: int = STEP, fraction: float = BORDER_FRACTION) -> CameraMotion:
    """Measure the background's composed motion in a clip relative to its first frame.

    Each sampled pair of frames is aligned with a similarity transform of the background band;
    the transforms are chained from frame 0. A pair with too few matches is skipped and counted,
    because a skipped pair can only understate the motion.

    Args:
        clip: Video file to read.
        step: Frames between sampled pairs.
        fraction: Width of the measured border band as a share of the frame.

    Returns:
        The per-step path and its summary.

    Raises:
        FileNotFoundError: If OpenCV cannot open the file.
    """
    capture = cv2.VideoCapture(str(clip))
    if not capture.isOpened():
        raise FileNotFoundError(f"cannot open video: {clip}")
    gray = []
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        gray.append(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
    capture.release()
    mask = border_mask(gray[0].shape, fraction)
    sift = cv2.SIFT_create(nfeatures=3000)
    cumulative = np.eye(3, dtype=np.float32)
    steps, per_pair, failed = [], [], 0
    for start in range(0, len(gray) - step, step):
        transform, inliers = pair_transform(gray[start], gray[start + step], mask, sift)
        if transform is None:
            failed += 1
            continue
        cumulative = transform @ cumulative
        scale = float(np.hypot(cumulative[0, 0], cumulative[1, 0]))
        steps.append(
            CameraStep(
                frame=start + step,
                inliers=inliers,
                scale=scale,
                rotation_deg=float(np.degrees(np.arctan2(cumulative[1, 0], cumulative[0, 0]))),
                tx=float(cumulative[0, 2]),
                ty=float(cumulative[1, 2]),
            )
        )
        per_pair.append(float(np.hypot(transform[0, 2], transform[1, 2])))
    if not steps:
        raise RuntimeError(f"no background fit in any pair of {clip}")
    return CameraMotion(
        frames=len(gray),
        step=step,
        steps=tuple(steps),
        failed_steps=failed,
        step_translation_px_median=median(per_pair),
        step_translation_px_max=max(per_pair),
        cumulative_translation_px_max=max(float(np.hypot(s.tx, s.ty)) for s in steps),
        scale_min=min(s.scale for s in steps),
        scale_max=max(s.scale for s in steps),
        rotation_deg_max=max(abs(s.rotation_deg) for s in steps),
        inliers_median=median(s.inliers for s in steps),
    )
