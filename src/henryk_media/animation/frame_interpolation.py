"""Convert a clip to a fixed frame rate with FILM, the frame-interpolation model in ComfyUI core.

The image-to-video models render 5 s at their native rate (24 or 16 fps); the notebooks deliver
30 fps. This module runs as a worker under ComfyUI's own environment, which holds the pinned FILM
model code in ``comfy_extras/frame_interpolation_models`` and a matching PyTorch build:

    models/photo-animation/ComfyUI/.venv/bin/python \
        src/henryk_media/animation/frame_interpolation.py \
        --input native.mp4 --output clip.mp4 --frames 150 \
        --model models/photo-animation/ComfyUI/models/frame_interpolation/film_net_fp16.safetensors

It decodes the native clip, synthesizes every output frame at its exact time on the output grid
with FILM's continuous timestep, and encodes an H.264 mp4. A frame that falls on a native frame
time is that native frame, never a synthesized copy. The module imports nothing from
``henryk_media``, so ComfyUI's environment needs only its own dependencies.
"""

import argparse
from collections.abc import Iterable
from fractions import Fraction
from pathlib import Path
import time

import cv2
import numpy as np

DEFAULT_FPS = 30.0
DEFAULT_FRAMES = 150


def schedule(
    native_frames: int, native_fps: float, fps: float, frames: int
) -> list[tuple[int, float]]:
    """Return, per output frame, the native frame before it and the fraction to the next.

    Args:
        native_frames: Frame count of the native clip.
        native_fps: Frame rate of the native clip.
        fps: Output frame rate.
        frames: Output frame count.

    Returns:
        ``(native index, fraction)`` per output frame, in output order. Fraction 0 means the
        output frame is the native frame itself; any other value is FILM's timestep in the pair
        starting at ``native index``.

    Raises:
        ValueError: If the clip has fewer than two frames, or an output frame lies past the
            clip's last native frame.
    """
    if native_frames < 2:
        raise ValueError(f"a clip with {native_frames} frame(s) cannot be interpolated")
    last = (native_frames - 1) / native_fps
    steps: list[tuple[int, float]] = []
    for index in range(frames):
        moment = index / fps
        if moment > last + 1e-9:
            raise ValueError(
                f"output frame {index} at {moment:.3f} s lies past the clip's last frame "
                f"at {last:.3f} s"
            )
        position = moment * native_fps
        pair = int(position)
        fraction = position - pair
        if fraction < 1e-9:
            steps.append((pair, 0.0))
        elif 1 - fraction < 1e-9:
            steps.append((pair + 1, 0.0))
        else:
            steps.append((pair, round(fraction, 9)))
    return steps


def pairs(steps: Iterable[tuple[int, float]]) -> dict[int, list[tuple[int, float]]]:
    """Group synthesized frames by their native pair: pair index -> [(output index, fraction)]."""
    grouped: dict[int, list[tuple[int, float]]] = {}
    for output_index, (pair, fraction) in enumerate(steps):
        if fraction:
            grouped.setdefault(pair, []).append((output_index, fraction))
    return grouped


def read_frames(path: Path) -> tuple[list[np.ndarray], float]:
    """Return the clip's frames as RGB uint8 arrays and its declared frame rate.

    Raises:
        FileNotFoundError: If OpenCV cannot open the file.
        ValueError: If the file holds no frame.
    """
    capture = cv2.VideoCapture(str(path))
    if not capture.isOpened():
        raise FileNotFoundError(f"cannot open video: {path}")
    native_fps = capture.get(cv2.CAP_PROP_FPS)
    frames = []
    while True:
        ok, frame = capture.read()
        if not ok:
            break
        frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))  # OpenCV decodes BGR
    capture.release()
    if not frames:
        raise ValueError(f"no frames decoded from {path}")
    return frames, native_fps


def main() -> None:
    """Interpolate one clip and write it; see the module docstring for the command."""
    parser = argparse.ArgumentParser(description="Interpolate a clip with ComfyUI's FILM model.")
    parser.add_argument("--input", type=Path, required=True, help="native clip to convert")
    parser.add_argument("--output", type=Path, required=True, help="30 fps clip to write")
    parser.add_argument("--model", type=Path, required=True, help="FILM or RIFE checkpoint")
    parser.add_argument("--fps", type=float, default=DEFAULT_FPS, help="output frame rate")
    parser.add_argument("--frames", type=int, default=DEFAULT_FRAMES, help="output frame count")
    arguments = parser.parse_args()

    # Heavy imports stay here: only ComfyUI's environment has them.
    import av
    import comfy.utils
    from comfy_extras.nodes_frame_interpolation import FrameInterpolationModelLoader
    import torch

    native, native_fps = read_frames(arguments.input)
    steps = schedule(len(native), native_fps, arguments.fps, arguments.frames)

    device = torch.device("cuda")
    dtype = torch.float16
    # ComfyUI's own loader accepts FILM and RIFE checkpoints; the checkout is pinned.
    model = FrameInterpolationModelLoader._detect_and_load(
        comfy.utils.load_torch_file(str(arguments.model), safe_load=True)
    )
    model.eval().to(device=device, dtype=dtype)

    def frame_tensor(index: int) -> "torch.Tensor":
        """Return a native frame as a one-image float batch on the GPU."""
        image = torch.from_numpy(native[index]).permute(2, 0, 1).unsqueeze(0)
        return image.to(device).float().div_(255).to(dtype)

    start = time.perf_counter()
    output: list[np.ndarray | None] = [None] * arguments.frames
    for output_index, (pair, fraction) in enumerate(steps):
        if fraction == 0.0:
            output[output_index] = native[pair]
    features: dict[int, object] = {}
    # No gradients are needed; recording them would keep every activation alive.
    with torch.inference_mode():
        for pair, group in pairs(steps).items():
            for index in (pair, pair + 1):
                if index not in features:
                    features[index] = model.extract_features(frame_tensor(index))
            images = model.forward_multi_timestep(
                frame_tensor(pair),
                frame_tensor(pair + 1),
                [fraction for _, fraction in group],
                cache={"img0": features[pair], "img1": features[pair + 1]},
            )
            for (output_index, _), image in zip(group, images, strict=True):
                pixels = (image.clamp(0.0, 1.0) * 255).round().to(torch.uint8)
                output[output_index] = pixels.permute(1, 2, 0).cpu().numpy()
            features = {index: value for index, value in features.items() if index >= pair}
    if any(image is None for image in output):
        raise RuntimeError("the frame schedule left an output frame empty")

    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    container = av.open(str(arguments.output), "w", format="mp4")
    stream = container.add_stream("libx264", rate=Fraction(arguments.fps).limit_denominator(1001))
    stream.width, stream.height = native[0].shape[1], native[0].shape[0]
    stream.pix_fmt = "yuv420p"
    stream.options = {"crf": "17", "preset": "medium"}
    for image in output:
        for packet in stream.encode(av.VideoFrame.from_ndarray(image, format="rgb24")):
            container.mux(packet)
    for packet in stream.encode():
        container.mux(packet)
    container.close()
    print(
        f"interpolated {len(native)} frames at {native_fps:g} fps into {len(output)} frames at "
        f"{arguments.fps:g} fps in {time.perf_counter() - start:.1f} s: {arguments.output}"
    )


if __name__ == "__main__":
    main()
