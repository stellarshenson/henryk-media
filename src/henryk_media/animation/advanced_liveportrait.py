"""LivePortrait through ComfyUI-AdvancedLivePortrait: idle motion from keyframed expressions.

The node pack needs no driving clip. Each keyframe is an ExpressionEditor node holding expression
values (smile, blink, head rotation in degrees); the AdvancedLivePortrait node blends linearly from
one keyframe to the next and pastes the animated face crop back into the photo. It animates only
the face nearest the photo's horizontal centre. Head scale and position are never changed: the
editors set rotation and expression only.

ComfyUI runs from its own environment (``models/photo-animation/ComfyUI/.venv``, torch built for
CUDA 13.0) as a server on 127.0.0.1, started here as a detached process pinned to one GPU. Every
render moves the files it added or changed in ComfyUI's input, output and temp folders to the
trash, so no copy of a photo stays there.
"""

import atexit
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime
from http.client import HTTPException
import itertools
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.request

import numpy as np

from henryk_media.animation.common import (
    Box,
    ClipResult,
    load_result,
    probe_clip,
    project_relative,
    save_result,
)
from henryk_media.config import MODELS_DIR, PROJ_ROOT

MODEL = "LivePortrait via ComfyUI-AdvancedLivePortrait"
COMFYUI_DIR = MODELS_DIR / "photo-animation" / "ComfyUI"
NODE_PACKS = ("ComfyUI-AdvancedLivePortrait", "ComfyUI-VideoHelperSuite")
WEIGHTS_METADATA = {  # hf download records the revision as the first line of each .metadata file
    "Kijai/LivePortrait_safetensors": "models/liveportrait/.cache/huggingface/download/"
    "spade_generator.safetensors.metadata",
    "Bingsu/adetailer face_yolov8n.pt": "models/ultralytics/.cache/huggingface/download/"
    "face_yolov8n.pt.metadata",
}
WORK_FOLDERS = ("input", "output", "temp")  # where ComfyUI keeps copies of the photo
GPU_UUID = "GPU-1223ff00-ce71-874f-592e-a4429e9f47ba"  # nvidia-smi index 2, RTX PRO 5000 Blackwell
PORT = 8188
SERVER = f"http://127.0.0.1:{PORT}"
SERVER_LOG = PROJ_ROOT / "logs" / "comfyui-server.log"
LAUNCH_ARGS = [
    ".venv/bin/python",
    "main.py",
    "--listen",
    "127.0.0.1",
    "--port",
    str(PORT),
    "--disable-auto-launch",
    "--offline",
    "--disable-product-tips",
    "--feature-flag",
    "enable_telemetry=false",
]
LAUNCH_ENV = {
    "CUDA_DEVICE_ORDER": "PCI_BUS_ID",
    "CUDA_VISIBLE_DEVICES": GPU_UUID,
    "HF_HUB_OFFLINE": "1",
    "YOLO_OFFLINE": "1",
}
START_TIMEOUT_SECONDS = 180
POLL_SECONDS = 0.1
MIB = 2**20
BYTES_PER_GB = 1e9

# Timeline of every clip: 5 s at 30 fps
FPS = 30
FRAMES = 150
KEYFRAME_STEP = 2  # frames between keyframes sampling the eased curves
# Curves as (frame, fraction of the variant's peak) knots, each a turning point of its curve.
# Consecutive knots never share a value, so no curve holds; knots past frame 149 keep every curve
# moving to the end of the clip.
# Smile: builds over 0-1.8 s, then eases back to 60 % and 70 % of the peak and returns, 1 s each
SMILE_KNOTS = ((0, 0.0), (54, 1.0), (84, 0.6), (114, 1.0), (144, 0.7), (174, 1.0))
# Head: side-to-side turns of 1.2-1.4 s; the pitch and roll turns fall between the yaw turns, so
# the head never stops. Pitch stays between 0 and the peak: positive lowers the chin, so the chin
# never rises above the photo's pose
YAW_KNOTS = ((0, 0.0), (36, 0.75), (78, -0.55), (120, 1.0), (162, 0.1))
PITCH_KNOTS = ((0, 0.0), (22, 0.45), (57, 0.0), (99, 1.0), (141, 0.3), (180, 0.8))
ROLL_KNOTS = ((0, 0.0), (24, -0.5), (66, 1.0), (108, -0.6), (150, 0.8), (190, 0.0))
BLINK_START = 60  # 2.0 s
# (frame offset from BLINK_START, fraction of the closed value): 4 frames closing, 2 frames
# closed, 6 frames opening - 11 frame steps, 0.37 s from open to open
BLINK_SHAPE = ((0, 0.0), (4, 1.0), (5, 1.0), (11, 0.0))
CROP_FACTOR = 1.7  # face crop size relative to the detected face box, the node's default

EDITOR_INPUTS = {  # ExpressionEditor sliders; a keyframe overrides the first five
    "smile": 0,
    "rotate_yaw": 0,
    "rotate_pitch": 0,
    "rotate_roll": 0,
    "blink": 0,
    "eyebrow": 0,
    "wink": 0,
    "pupil_x": 0,
    "pupil_y": 0,
    "aaa": 0,
    "eee": 0,
    "woo": 0,
    "src_ratio": 1,
    "sample_ratio": 1,
    "sample_parts": "OnlyExpression",
    "crop_factor": CROP_FACTOR,
}

Keyframe = tuple[int, dict[str, float]]  # (frame index, ExpressionEditor values)
Knots = tuple[tuple[int, float], ...]  # (frame, value) pairs with increasing frames


@dataclass(frozen=True)
class Motion:
    """Peak values of one idle motion, in the ExpressionEditor's units.

    Each value scales the knot fractions of its curve; the largest fraction of every curve is 1.

    Attributes:
        smile: Largest smile (slider -0.3 to 1.3).
        yaw: Largest side-to-side head turn, degrees.
        pitch: Largest up-and-down head rotation, degrees; positive lowers the chin (the node
            moves the facial features down), negative lifts it.
        roll: Largest head tilt, degrees.
        blink: Eyelid value at the closed point of the one blink (slider -20 to 5, negative
            closes); 0 means no blink.
    """

    smile: float
    yaw: float
    pitch: float
    roll: float
    blink: float


def ease(x: float) -> float:
    """Return the cosine-eased fraction (1 - cos πx) / 2 of x clamped to [0, 1].

    Zero slope at both ends, like a pendulum at its turning point, and no lingering near them.
    """
    x = min(max(x, 0.0), 1.0)
    return (1 - math.cos(math.pi * x)) / 2


def eased(frame: int, knots: Knots) -> float:
    """Return a knot curve at one frame: eased from each knot to the next, held after the last.

    Args:
        frame: Frame index.
        knots: (frame, value) pairs with increasing frames.
    """
    for (start, before), (end, after) in itertools.pairwise(knots):
        if frame < end:
            return before + (after - before) * ease((frame - start) / (end - start))
    return knots[-1][1]


def expression_at(frame: int, motion: Motion) -> dict[str, float]:
    """Return the ExpressionEditor values of the motion at one frame.

    The smile, yaw, pitch and roll each follow their own knot curve (SMILE_KNOTS, YAW_KNOTS,
    PITCH_KNOTS, ROLL_KNOTS) scaled by the motion's peak value. The blink follows BLINK_SHAPE.
    """
    offsets, fractions = zip(*BLINK_SHAPE, strict=True)
    closure = float(np.interp(frame - BLINK_START, offsets, fractions, left=0.0, right=0.0))
    values = {
        "smile": motion.smile * eased(frame, SMILE_KNOTS),
        "rotate_yaw": motion.yaw * eased(frame, YAW_KNOTS),
        "rotate_pitch": motion.pitch * eased(frame, PITCH_KNOTS),
        "rotate_roll": motion.roll * eased(frame, ROLL_KNOTS),
        "blink": motion.blink * closure,
    }
    return {name: round(value, 4) for name, value in values.items()}


def head_steps(motion: Motion) -> list[float]:
    """Return the head rotation between each frame and the next, in degrees.

    Each step is the Euclidean norm of the yaw, pitch and roll changes; 0 means the head holds.
    """
    poses = np.array(
        [
            [values["rotate_yaw"], values["rotate_pitch"], values["rotate_roll"]]
            for values in (expression_at(frame, motion) for frame in range(FRAMES))
        ]
    )
    return np.linalg.norm(np.diff(poses, axis=0), axis=1).tolist()


def keyframes(motion: Motion) -> list[Keyframe]:
    """Return the motion's keyframes: every KEYFRAME_STEP frames, the last frame and the blink.

    Frame 0 holds the photo's own expression (all values 0). The blink adds its BLINK_SHAPE frames
    only when ``motion.blink`` is not 0.
    """
    frames = set(range(0, FRAMES, KEYFRAME_STEP)) | {FRAMES - 1}
    if motion.blink:
        frames |= {BLINK_START + offset for offset, _ in BLINK_SHAPE}
    return [(frame, expression_at(frame, motion)) for frame in sorted(frames)]


def knot_text(knots: Knots) -> str:
    """Return knots as ``frame:value`` pairs separated by spaces, as the sidecars record them."""
    return " ".join(f"{frame}:{value:g}" for frame, value in knots)


def settings(motion: Motion) -> dict[str, object]:
    """Return the sidecar settings of a motion: peak values, curve knots, keyframes, crop factor.

    Strings keep the record equal after a JSON round trip, so ``restore`` can compare it.
    """
    return {
        **asdict(motion),
        "smile_knots": knot_text(SMILE_KNOTS),
        "yaw_knots": knot_text(YAW_KNOTS),
        "pitch_knots": knot_text(PITCH_KNOTS),
        "roll_knots": knot_text(ROLL_KNOTS),
        "blink_start_frame": BLINK_START if motion.blink else "none",
        "keyframe_step": KEYFRAME_STEP,
        "crop_factor": CROP_FACTOR,
    }


def command(frames: list[int]) -> str:
    """Return the AdvancedLivePortrait command that reaches keyframe k at frame ``frames[k]``.

    Each line is ``index=change:keep``. Line 0 shows the photo's own expression (index 0) on frame
    0; line k blends linearly from keyframe k - 1 to editor k over ``frames[k] - frames[k - 1]``
    frames with no hold, so the clip has ``frames[-1] + 1`` frames.

    Raises:
        ValueError: If frames does not start at 0 or is not strictly increasing.
    """
    if frames[0] != 0 or any(b <= a for a, b in itertools.pairwise(frames)):
        raise ValueError(f"keyframe frames must start at 0 and increase: {frames}")
    steps = [f"{k}={b - a}:0" for k, (a, b) in enumerate(itertools.pairwise(frames), start=1)]
    return "\n".join(["0=1:0", *steps])


def build_graph(image: str, frames_values: list[Keyframe], prefix: str) -> dict[str, dict]:
    """Return the ComfyUI API graph that renders one clip.

    Node 1 loads ``image`` from ComfyUI's input folder. Nodes 2 to n + 1 are one ExpressionEditor
    per keyframe after frame 0, chained through ``motion_link``, so editor k is command index k.
    Node n + 2 is AdvancedLivePortrait with the keyframe command, node n + 3 writes an H.264 mp4 at
    FPS named ``<prefix>_00001.mp4`` into ComfyUI's output folder.

    Args:
        image: File name inside ComfyUI's input folder.
        frames_values: Keyframes as returned by ``keyframes``; keyframe 0 is frame 0, the photo.
        prefix: VideoHelperSuite file name prefix.

    Raises:
        ValueError: If there is no keyframe after frame 0 or the frames are not increasing.
    """
    if len(frames_values) < 2:
        raise ValueError("at least one keyframe after frame 0 is needed")
    graph: dict[str, dict] = {"1": {"class_type": "LoadImage", "inputs": {"image": image}}}
    link: dict[str, list] = {"src_image": ["1", 0]}
    for node, (_, values) in enumerate(frames_values[1:], start=2):
        inputs = {**EDITOR_INPUTS, **values, **link}
        graph[str(node)] = {"class_type": "ExpressionEditor", "inputs": inputs}
        link = {"motion_link": [str(node), 1]}
    animate = str(len(graph) + 1)
    graph[animate] = {
        "class_type": "AdvancedLivePortrait",
        "inputs": {
            **link,
            "retargeting_eyes": 0,
            "retargeting_mouth": 0,
            "crop_factor": CROP_FACTOR,
            "turn_on": True,
            "tracking_src_vid": False,
            "animate_without_vid": True,
            "command": command([frame for frame, _ in frames_values]),
        },
    }
    graph[str(len(graph) + 1)] = {
        "class_type": "VHS_VideoCombine",
        "inputs": {
            "images": [animate, 0],
            "frame_rate": FPS,
            "loop_count": 0,
            "filename_prefix": prefix,
            "format": "video/h264-mp4",
            "pix_fmt": "yuv420p",
            "crf": 19,
            "save_metadata": False,
            "trim_to_audio": False,
            "pingpong": False,
            "save_output": True,
        },
    }
    return graph


def api(path: str, payload: dict | None = None) -> dict:
    """GET a ComfyUI endpoint, or POST ``payload`` as JSON, and return the decoded JSON reply.

    Raises:
        RuntimeError: If the server answers with an HTTP error; the message carries its body,
            which names the failing node for a rejected graph.
    """
    data = None if payload is None else json.dumps(payload).encode()
    request = urllib.request.Request(SERVER + path, data=data)
    try:
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"ComfyUI {path}: HTTP {error.code} {error.read().decode()}") from error


def server_answers() -> bool:
    """Return True when a server answers on SERVER."""
    try:
        api("/system_stats")
    except (urllib.error.URLError, ConnectionError, HTTPException):
        return False
    return True


def logged_faces(log: str) -> tuple[int, list[Box]]:
    """Return the face count YOLO reports and the face boxes the node prints while picking a face.

    The node walks YOLO's boxes and prints a box each time it lies nearer the photo's horizontal
    centre than the boxes before it, so the last printed box is the face it animates. A face that
    is not nearer than an earlier one is not printed; compare the box count with the face count.

    Raises:
        ValueError: If the log holds no face detection.
    """
    counts = re.findall(r"^\d+: \d+x\d+ (\d+) faces?", log, re.MULTILINE)
    boxes = []
    for line in log.splitlines():
        if "best_box:" in line:
            inside = line[line.index("[") + 1 : line.rindex("]")].replace("np.float32", "")
            x0, y0, x1, y1 = (round(float(value)) for value in re.findall(r"-?[\d.]+", inside))
            boxes.append((x0, y0, x1, y1))
    if not counts or not boxes:
        raise ValueError("the ComfyUI log holds no face detection")
    return int(counts[-1]), boxes


def gpu_memory_used_mib() -> int:
    """Return the memory in use on the pinned GPU in MiB, as nvidia-smi reports it."""
    query = [
        "nvidia-smi",
        "-i",
        GPU_UUID,
        "--query-gpu=memory.used",
        "--format=csv,noheader,nounits",
    ]
    return int(subprocess.run(query, capture_output=True, text=True, check=True).stdout)


def work_files() -> dict[Path, int]:
    """Return every file in ComfyUI's input, output and temp folders with its modification time."""
    return {
        path: path.stat().st_mtime_ns
        for folder in WORK_FOLDERS
        for path in (COMFYUI_DIR / folder).rglob("*")
        if path.is_file()
    }


def trash(paths: list[Path]) -> None:
    """Move the files that exist among ``paths`` to the trash with trash-put."""
    existing = [str(path) for path in paths if path.exists()]
    if existing:
        subprocess.run(["trash-put", *existing], check=True)


def git_head(repo: Path) -> str:
    """Return the commit hash checked out in a git clone."""
    head = ["git", "-C", str(repo), "rev-parse", "HEAD"]
    return subprocess.run(head, capture_output=True, text=True, check=True).stdout.strip()


def revision() -> str:
    """Return the commits of ComfyUI and both node packs and the revisions of the weights."""
    repos = [COMFYUI_DIR, *(COMFYUI_DIR / "custom_nodes" / pack for pack in NODE_PACKS)]
    commits = [f"{repo.name}@{git_head(repo)}" for repo in repos]
    weights = [
        f"{name}@{(COMFYUI_DIR / path).read_text().splitlines()[0]}"
        for name, path in WEIGHTS_METADATA.items()
    ]
    return f"code {', '.join(commits)}; weights {', '.join(weights)}"


class ComfyUI:
    """A ComfyUI server on the pinned GPU, started on construction and stopped by ``stop``.

    The server is also stopped when the Python process exits, so a failed notebook run does not
    leave it holding the GPU.

    Raises:
        RuntimeError: If a server already answers on the port, or the server exits while starting.
        TimeoutError: If the server does not answer within START_TIMEOUT_SECONDS.
    """

    def __init__(self) -> None:
        if server_answers():
            raise RuntimeError(f"a server already answers on {SERVER}; stop it first")
        self.baseline_mib = gpu_memory_used_mib()
        SERVER_LOG.parent.mkdir(exist_ok=True)
        with SERVER_LOG.open("w") as log:
            self.process = subprocess.Popen(
                LAUNCH_ARGS,
                cwd=COMFYUI_DIR,
                env={**os.environ, **LAUNCH_ENV},
                stdin=subprocess.DEVNULL,
                stdout=log,
                stderr=subprocess.STDOUT,
                start_new_session=True,  # detached like setsid: no signal from the notebook's terminal
            )
        atexit.register(self.stop)
        deadline = time.monotonic() + START_TIMEOUT_SECONDS
        while not server_answers():
            if self.process.poll() is not None:
                raise RuntimeError(
                    f"ComfyUI exited with code {self.process.returncode}, see {SERVER_LOG}"
                )
            if time.monotonic() > deadline:
                self.stop()
                raise TimeoutError(f"ComfyUI did not answer within {START_TIMEOUT_SECONDS} s")
            time.sleep(1)
        self.stats = api("/system_stats")  # ComfyUI, PyTorch and device as the server reports them
        self.revision = revision()

    def stop(self) -> None:
        """Stop the server and wait for it to exit; does nothing when it has already exited."""
        if self.process.poll() is None:
            self.process.terminate()
            self.process.wait(timeout=60)

    def run(self, graph: dict[str, dict]) -> tuple[dict, float, int]:
        """Submit a graph and wait for it to finish.

        Returns:
            (its history entry, wall seconds from submission to the finished entry, highest GPU
            memory in MiB sampled with nvidia-smi while it ran).

        Raises:
            RuntimeError: If the graph is rejected, fails, or the server exits while it runs.
        """
        peak_mib = gpu_memory_used_mib()
        start = time.perf_counter()
        prompt_id = api("/prompt", {"prompt": graph})["prompt_id"]
        while prompt_id not in (history := api(f"/history/{prompt_id}")):
            if self.process.poll() is not None:
                raise RuntimeError(f"ComfyUI exited during the render, see {SERVER_LOG}")
            peak_mib = max(peak_mib, gpu_memory_used_mib())
            time.sleep(POLL_SECONDS)
        seconds = time.perf_counter() - start
        entry = history[prompt_id]
        if entry["status"]["status_str"] != "success":
            raise RuntimeError(f"ComfyUI render failed: {entry['status']['messages']}")
        return entry, seconds, peak_mib

    @contextmanager
    def photo_copy(self, source: Path, image: str) -> Iterator[None]:
        """Place a copy of ``source`` in ComfyUI's input folder as ``image`` for one graph.

        On exit, also after an error, every file added or changed in ComfyUI's input, output and
        temp folders since entry goes to the trash.
        """
        before = work_files()
        shutil.copyfile(source, COMFYUI_DIR / "input" / image)
        try:
            yield
        finally:
            trash([path for path, mtime in work_files().items() if before.get(path) != mtime])

    def detect_faces(self, source: Path) -> tuple[int, list[Box]]:
        """Return the faces the node finds in a photo, as ``logged_faces`` reads them.

        Runs one ExpressionEditor with every slider at 0, which detects the face the way a render
        does, and reads the lines it writes from the server's in-memory log, which records every
        write as it happens. The log file is no use here: the node's prints reach it only when a
        later log record flushes stdout, so it lags one prompt behind. Boxes are in photo pixels.
        """
        image = f"{source.stem}--faces{source.suffix}"
        graph = {
            "1": {"class_type": "LoadImage", "inputs": {"image": image}},
            "2": {
                "class_type": "ExpressionEditor",
                "inputs": {**EDITOR_INPUTS, "src_image": ["1", 0]},
            },
        }
        start = datetime.now()  # the server stamps log entries with the same local clock
        with self.photo_copy(source, image):
            self.run(graph)
        entries = api("/internal/logs/raw")["entries"]
        return logged_faces(
            "".join(entry["m"] for entry in entries if datetime.fromisoformat(entry["t"]) >= start)
        )

    def render(self, source: Path, motion: Motion, variant: str, clip: Path) -> ClipResult:
        """Animate one photo with one motion and save the clip, its sidecar and its checkpoint.

        The photo is copied into ComfyUI's folders only for the render (see ``photo_copy``). An
        existing clip and sidecar at ``clip`` go to the trash before the new clip replaces them.

        Args:
            source: Photo to animate.
            motion: Peak values of the idle motion.
            variant: Variant name recorded in the sidecar.
            clip: Destination ``.mp4``; the sidecar and checkpoint are written beside it.

        Returns:
            The clip's provenance and measurements, also saved as sidecar and checkpoint.
        """
        frames_values = keyframes(motion)
        image = f"{clip.stem}{source.suffix}"
        with self.photo_copy(source, image):
            entry, seconds, peak_mib = self.run(build_graph(image, frames_values, clip.stem))
            video = next(
                item
                for output in entry["outputs"].values()
                for item in output.get("gifs", [])
                if item["filename"].endswith(".mp4")
            )
            clip.parent.mkdir(parents=True, exist_ok=True)
            trash([clip, clip.with_suffix(".md")])
            shutil.move(COMFYUI_DIR / video["type"] / video["subfolder"] / video["filename"], clip)
        width, height, frames, fps = probe_clip(clip)
        result = ClipResult(
            clip=project_relative(clip),
            source=project_relative(source),
            driving="",
            model=MODEL,
            revision=self.revision,
            variant=variant,
            settings=settings(motion),
            gpu=self.stats["devices"][0]["name"],
            seconds=round(seconds, 2),
            peak_vram_gb=round((peak_mib - self.baseline_mib) * MIB / BYTES_PER_GB, 3),
            width=width,
            height=height,
            frames=frames,
            fps=fps,
            time_scope="POST /prompt to the finished history entry: face detection, keyframe "
            "editors, frame rendering, paste-back and H.264 encode",
            vram_scope="nvidia-smi memory.used of the GPU sampled during the render, minus the "
            "memory in use before the ComfyUI server started",
        )
        save_result(result, clip)
        return result


def restore(clip: Path, motion: Motion) -> ClipResult | None:
    """Return the saved result of a finished clip rendered with this motion, else None.

    A clip whose checkpoint records other settings (peak values, curves or keyframes) is not
    restored, so a changed variant or timeline is rendered again instead of being taken from an
    earlier run.
    """
    result = load_result(clip)
    if result is None or result.settings != settings(motion):
        return None
    return result
