"""LivePortrait (humans) wrapper: load the pipeline once, then render one photo per call.

LivePortrait is not an installed package. Its code is the ``src`` folder of the clone in
``models/photo-animation/LivePortrait``, imported with the clone root on ``sys.path``.

Two traps of the command-line entry point do not apply here:

- ffmpeg: ``inference.py`` finds ffmpeg only when it runs from the clone directory. The Python API
  writes video through the ffmpeg binary bundled with imageio-ffmpeg and never calls ``ffmpeg``
  by name; the missing ffprobe only turns off the copy of audio from the driving clip
- Motion template: LivePortrait writes ``<driving name>.pkl`` beside the driving clip. Every
  render reads a copy of the driving clip in a temporary directory, so no ``.pkl`` lands in
  ``data/``. The same directory receives LivePortrait's side-by-side concat video, which is
  discarded with it; only the result video is kept
"""

from dataclasses import replace
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

import cv2
import torch

from henryk_media.animation.advanced_liveportrait import trash
from henryk_media.animation.common import (
    Box,
    ClipResult,
    load_working_copy,
    measure,
    probe_clip,
    project_relative,
    save_result,
)
from henryk_media.config import MODELS_DIR

MODEL = "LivePortrait"
REPO_DIR = MODELS_DIR / "photo-animation" / "LivePortrait"
# hf download --local-dir records the downloaded revision as the first line of each .metadata file
WEIGHTS_METADATA = (
    REPO_DIR
    / "pretrained_weights/.cache/huggingface/download/liveportrait/base_models"
    / "spade_generator.pth.metadata"
)
ANIMATED_FACE_BGR = (113, 204, 46)  # palette tertiary #2ECC71: the face LivePortrait animates
OTHER_FACE_BGR = (60, 76, 231)  # palette secondary #E74C3C: faces LivePortrait leaves still


def _no_bar[T](sequence: T, *_args: object, **_kwargs: object) -> T:
    """Stand-in for rich.progress.track: iterate without drawing a bar."""
    return sequence


class LivePortrait:
    """LivePortrait humans pipeline, loaded once and reused for every render.

    Args:
        **settings: ``ArgumentConfig`` fields that override LivePortrait's command-line
            defaults, for example ``flag_pasteback=True`` or ``source_max_dim=0``.
    """

    def __init__(self, **settings: object) -> None:
        if str(REPO_DIR) not in sys.path:
            sys.path.insert(0, str(REPO_DIR))
        from inference import partial_fields
        from src import live_portrait_pipeline
        from src.config.argument_config import ArgumentConfig
        from src.config.crop_config import CropConfig
        from src.config.inference_config import InferenceConfig
        from src.utils import rprint, video

        # LivePortrait logs every step and draws a rich bar per stage; the notebook draws its own
        rprint.console.quiet = True
        live_portrait_pipeline.track = video.track = _no_bar

        self.settings = settings
        self.args = ArgumentConfig(**settings)
        self.pipeline = live_portrait_pipeline.LivePortraitPipeline(
            inference_cfg=partial_fields(InferenceConfig, self.args.__dict__),
            crop_cfg=partial_fields(CropConfig, self.args.__dict__),
        )
        commit = subprocess.run(
            ["git", "-C", str(REPO_DIR), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        weights = WEIGHTS_METADATA.read_text().splitlines()[0]
        self.revision = (
            f"code KwaiVGI/LivePortrait@{commit}, weights KlingTeam/LivePortrait@{weights}"
        )

    def detect_faces(self, source: Path) -> list[tuple[Box, float]]:
        """Return (box, detector score) for each face LivePortrait finds, in its pick order.

        LivePortrait animates only the first face (largest box first). The boxes are in
        working-copy pixels, which are the clip's pixels while ``source_max_dim`` leaves the photo
        unscaled.
        """
        bgr = cv2.cvtColor(load_working_copy(source), cv2.COLOR_RGB2BGR)
        height, width = bgr.shape[:2]
        crop_cfg = self.pipeline.cropper.crop_cfg
        faces = self.pipeline.cropper.face_analysis_wrapper.get(
            bgr,
            flag_do_landmark_2d_106=False,
            direction=crop_cfg.direction,
            max_face_num=crop_cfg.max_face_num,
        )
        detections = []
        for face in faces:
            x0, y0, x1, y1 = (int(value) for value in face.bbox)
            # detector boxes can reach past the image edge; clamp so they slice the image correctly
            box = (max(x0, 0), max(y0, 0), min(x1, width), min(y1, height))
            detections.append((box, float(face.det_score)))
        return detections

    def render(self, source: Path, driving: Path, region: str, clip: Path) -> ClipResult:
        """Animate one working copy with one driving clip and save the result video as ``clip``.

        Args:
            source: Working copy to animate.
            driving: Driving video; motion is taken relative to its first frame.
            region: LivePortrait ``animation_region``, also the variant name: ``all`` moves
                expression and head pose, ``exp`` moves expression and eyes with the head still.
            clip: Destination ``.mp4``; the sidecar and checkpoint are written beside it.

        Returns:
            The clip's provenance and measurements, also saved as sidecar and checkpoint.
        """
        self.pipeline.live_portrait_wrapper.inference_cfg.animation_region = region
        with tempfile.TemporaryDirectory() as work:
            driving_copy = Path(work) / driving.name
            shutil.copyfile(driving, driving_copy)
            args = replace(
                self.args,
                source=str(source),
                driving=str(driving_copy),
                output_dir=work,
                animation_region=region,
            )
            (video, _concat), seconds, peak_vram_gb = measure(lambda: self.pipeline.execute(args))
            clip.parent.mkdir(parents=True, exist_ok=True)
            trash([clip, clip.with_suffix(".md")])
            shutil.move(video, clip)
        width, height, frames, fps = probe_clip(clip)
        result = ClipResult(
            clip=project_relative(clip),
            source=project_relative(source),
            driving=project_relative(driving),
            model=MODEL,
            revision=self.revision,
            variant=region,
            settings={**self.settings, "animation_region": region},
            gpu=torch.cuda.get_device_name(0),
            seconds=round(seconds, 2),
            peak_vram_gb=round(peak_vram_gb, 3),
            width=width,
            height=height,
            frames=frames,
            fps=fps,
        )
        save_result(result, clip)
        return result


def save_face_overlay(source: Path, boxes: list[Box], path: Path) -> None:
    """Draw the numbered face boxes on a copy of the working copy and save it as a JPEG.

    Box 1, the face LivePortrait animates, is drawn green and labelled "animated"; the others red.
    """
    bgr = cv2.cvtColor(load_working_copy(source), cv2.COLOR_RGB2BGR)
    thickness = max(2, bgr.shape[1] // 300)
    for number, (x0, y0, x1, y1) in enumerate(boxes, start=1):
        colour = ANIMATED_FACE_BGR if number == 1 else OTHER_FACE_BGR
        label = f"{number} animated" if number == 1 else str(number)
        cv2.rectangle(bgr, (x0, y0), (x1, y1), colour, thickness)
        cv2.putText(
            bgr,
            label,
            (x0, max(y0 - 3 * thickness, 0)),
            cv2.FONT_HERSHEY_SIMPLEX,
            thickness / 3,
            colour,
            thickness,
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(path), bgr)
