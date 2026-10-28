"""Client for the whole-frame image-to-video notebooks (LTX-2.5, MiniMax H3, Wan2.2).

One setup file describes one model's server and one workflow-api graph. ``Server`` starts that
server from the setup's launch command on the setup's GPU, renders a working copy through the
graph, converts the native clip to 30 fps with FILM (``frame_interpolation``), records wall time
and peak VRAM, and stops the server. Every file the render added or changed in the server's input,
output and temp folders goes to the trash, so no copy of a photo or clip stays there.

The graph is filled from the values the notebook passes: a value replaces every graph string equal
to its marker, and the module sets ``{{IMAGE}}`` and ``{{FILENAME_PREFIX}}`` itself. A finished
clip whose checkpoint records the same model and settings is restored instead of rendered again.
"""

import atexit
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from http.client import HTTPException
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
import urllib.error
import urllib.request

from loguru import logger

from henryk_media.animation.advanced_liveportrait import COMFYUI_DIR, WORK_FOLDERS, trash
from henryk_media.animation.common import (
    ClipResult,
    load_result,
    probe_clip,
    project_relative,
    save_result,
)

FPS = 30
FRAMES = 300  # 10 s at 30 fps
INTERPOLATION = "FILM fp16 (Comfy-Org/Frame-Interpolation film_net_fp16.safetensors)"
FRAME_INTERPOLATION_SCRIPT = Path(__file__).with_name("frame_interpolation.py")
FRAME_INTERPOLATION_WEIGHT = COMFYUI_DIR / "models/frame_interpolation/film_net_fp16.safetensors"
COMFYUI_PYTHON = COMFYUI_DIR / ".venv/bin/python"
START_TIMEOUT_SECONDS = 180
STOP_TIMEOUT_SECONDS = 120
FREE_TIMEOUT_SECONDS = 120
REQUEST_TIMEOUT_SECONDS = 30
POLL_SECONDS = 0.5
INTERPOLATION_MIB = 6144  # FILM at 832x1104 peaked at 4746 MiB in the module's test
MIB = 2**20
BYTES_PER_GB = 1e9


@dataclass(frozen=True)
class Setup:
    """One model's server, graph and native rate, read from a ``setup-<key>.json`` file.

    Attributes:
        model: Model name recorded in the sidecar.
        revision: Weight files or repository commits recorded in the sidecar.
        gpu: nvidia-smi UUID of the GPU the server and the interpolation run on.
        port: Port of the server on 127.0.0.1.
        native_fps: Frame rate the graph renders before interpolation.
        launch_command: Shell command that starts the server detached.
        stop_command: Shell command that stops the server.
        io_dirs: The server's input, output and temp folders.
        graph: The workflow-api graph the server executes.
    """

    model: str
    revision: str
    gpu: str
    port: int
    native_fps: float
    launch_command: str
    stop_command: str
    io_dirs: dict[str, Path]
    graph: Path

    @classmethod
    def load(cls, path: Path) -> "Setup":
        """Return the setup recorded in a JSON file; ``gpu`` keeps only its UUID.

        ``revision`` falls back to the setup's ``repository`` string, which names the repository
        and its revision, when the setup records no separate revision.
        """
        data = json.loads(path.read_text())
        return cls(
            model=data["model"],
            revision=data.get("revision") or data["repository"],
            gpu=data["gpu"].split()[0],
            port=data["port"],
            native_fps=data["native_fps"],
            launch_command=data["launch_command"],
            stop_command=data["stop_command"],
            io_dirs={name: Path(value) for name, value in data["io_dirs"].items()},
            graph=Path(data["workflow_api_path"]),
        )


def fill(node: object, values: dict[str, object]) -> object:
    """Return a copy of a JSON value with every marker string replaced by its value."""
    if isinstance(node, dict):
        return {key: fill(value, values) for key, value in node.items()}
    if isinstance(node, list):
        return [fill(value, values) for value in node]
    return values.get(node, node) if isinstance(node, str) else node


def saved_video(entry: dict) -> dict:
    """Return the history record of the last mp4 a finished graph saved.

    Raises:
        RuntimeError: If the graph saved no mp4.
    """
    files = [
        item
        for output in entry["outputs"].values()
        for item in output.get("images", [])
        if item["filename"].endswith(".mp4")
    ]
    if not files:
        raise RuntimeError(f"the render saved no mp4; outputs: {entry['outputs']}")
    return files[-1]


def clip_settings(
    setup: Setup,
    values: dict[str, object],
    settings: dict[str, object],
    source: Path,
    target_frames: int = FRAMES,
) -> dict[str, object]:
    """Return the sidecar settings of one clip, ``target_frames`` at FPS.

    The graph values are recorded under the marker name in lowercase without braces
    (``{{NEGATIVE_PROMPT}}`` becomes ``negative_prompt``), followed by the model's own settings,
    the interpolation facts and the source file's mtime and size. Values keep their type, so a
    saved checkpoint compares equal after a JSON round trip and a finished clip is restored
    instead of rendered again; the source identity makes a frame rewritten in place at the same
    path force a re-render.
    """
    markers = {marker.strip("{}").lower(): value for marker, value in values.items()}
    source_stat = source.stat()
    return {
        **markers,
        **settings,
        "native_fps": setup.native_fps,
        "fps": FPS,
        "frames": target_frames,
        "interpolation": INTERPOLATION,
        "source_mtime_ns": source_stat.st_mtime_ns,
        "source_bytes": source_stat.st_size,
    }


def restore_matches(result: ClipResult, setup: Setup, settings: dict) -> bool:
    """Return True when a finished clip belongs to this model and its settings still match."""
    return (
        result.model == setup.model
        and result.revision == setup.revision
        and result.settings == settings
    )


def api(port: int, path: str, payload: dict | None = None) -> dict:
    """GET a ComfyUI endpoint on 127.0.0.1, or POST ``payload`` as JSON, and return its reply.

    Raises:
        RuntimeError: If the server answers with an HTTP error; the message carries its body,
            which names the failing node for a rejected graph.
    """
    data = None if payload is None else json.dumps(payload).encode()
    request = urllib.request.Request(f"http://127.0.0.1:{port}{path}", data=data)
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
            body = response.read()
            return json.loads(body) if body else {}  # /interrupt and /free answer 200, no body
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"ComfyUI {path}: HTTP {error.code} {error.read().decode()}") from error


def port_answers(port: int) -> bool:
    """Return True when a ComfyUI server answers on the port."""
    try:
        api(port, "/system_stats")
    except (urllib.error.URLError, ConnectionError, HTTPException):
        return False
    return True


def gpu_used_mib(uuid: str) -> int:
    """Return the memory in use on one GPU in MiB, as nvidia-smi reports it."""
    query = ["nvidia-smi", "-i", uuid, "--query-gpu=memory.used", "--format=csv,noheader,nounits"]
    return int(subprocess.run(query, capture_output=True, text=True, check=True).stdout)


def gpu_free_mib(uuid: str) -> int:
    """Return the free memory on one GPU in MiB, as nvidia-smi reports it."""
    query = ["nvidia-smi", "-i", uuid, "--query-gpu=memory.free", "--format=csv,noheader,nounits"]
    return int(subprocess.run(query, capture_output=True, text=True, check=True).stdout)


def interpolate(native: Path, clip: Path, gpu: str, target_frames: int = FRAMES) -> None:
    """Write ``clip`` at ``FPS`` with ``target_frames`` frames, interpolated from ``native``.

    The worker runs in ComfyUI's environment, which holds the pinned FILM model code and PyTorch
    build; it imports nothing from this package.

    Raises:
        subprocess.CalledProcessError: If the worker fails; its output is printed to the notebook.
    """
    environment = {
        **os.environ,
        "CUDA_DEVICE_ORDER": "PCI_BUS_ID",
        "CUDA_VISIBLE_DEVICES": gpu,
        "PYTHONPATH": str(COMFYUI_DIR),
    }
    command = [
        str(COMFYUI_PYTHON),
        str(FRAME_INTERPOLATION_SCRIPT),
        "--input",
        str(native),
        "--output",
        str(clip),
        "--model",
        str(FRAME_INTERPOLATION_WEIGHT),
        "--fps",
        str(FPS),
        "--frames",
        str(target_frames),
    ]
    subprocess.run(command, cwd=COMFYUI_DIR, env=environment, check=True)


class Server:
    """A ComfyUI server on one setup's GPU, started on construction and stopped by ``stop``.

    The server is also stopped when the Python process exits, so a failed notebook run does not
    leave it holding the GPU.

    Args:
        setup: The model's server, graph and native rate.

    Raises:
        RuntimeError: If a server already answers on the setup's port.
        FileNotFoundError: If the FILM weights are missing.
        TimeoutError: If the server does not answer within START_TIMEOUT_SECONDS.
    """

    def __init__(self, setup: Setup) -> None:
        if port_answers(setup.port):
            raise RuntimeError(f"a server already answers on port {setup.port}; stop it first")
        if not FRAME_INTERPOLATION_WEIGHT.exists():
            raise FileNotFoundError(
                f"{FRAME_INTERPOLATION_WEIGHT} is missing; run make comfyui_frame_interpolation"
            )
        self.setup = setup
        self.baseline_mib = gpu_used_mib(setup.gpu)
        subprocess.run(setup.launch_command, shell=True, check=True)
        atexit.register(self.stop)
        deadline = time.monotonic() + START_TIMEOUT_SECONDS
        while not port_answers(setup.port):
            if time.monotonic() > deadline:
                self.stop()
                log = re.search(r">\s*(\S+\.log)", setup.launch_command)
                raise TimeoutError(
                    f"the server did not answer on port {setup.port} within "
                    f"{START_TIMEOUT_SECONDS} s; see {log.group(1) if log else 'its launch log'}"
                )
            time.sleep(1)
        self.stats = api(setup.port, "/system_stats")  # ComfyUI, PyTorch and device it reports

    def stop(self) -> None:
        """Stop the server with the setup's stop command and wait for its port to close.

        Raises:
            TimeoutError: If the port still answers after STOP_TIMEOUT_SECONDS.
        """
        subprocess.run(self.setup.stop_command, shell=True, capture_output=True, check=False)
        if not port_answers(self.setup.port):
            return
        deadline = time.monotonic() + STOP_TIMEOUT_SECONDS
        while port_answers(self.setup.port):
            if time.monotonic() > deadline:
                raise TimeoutError(
                    f"the server on port {self.setup.port} did not stop within "
                    f"{STOP_TIMEOUT_SECONDS} s"
                )
            time.sleep(POLL_SECONDS)

    def answers(self) -> bool:
        """Return True when the setup's server answers on its port."""
        return port_answers(self.setup.port)

    def free_gpu(self) -> None:
        """Make room on the setup's GPU for the interpolation by unloading the server's models.

        ComfyUI keeps a finished prompt's models resident, and Wan2.2 leaves about 3 GB free on
        the 72 GB card. The server applies ``/free`` when its queue loop next wakes, so this waits
        until nvidia-smi reports INTERPOLATION_MIB free.

        Raises:
            TimeoutError: If the GPU does not have that room within FREE_TIMEOUT_SECONDS.
        """
        if gpu_free_mib(self.setup.gpu) >= INTERPOLATION_MIB:
            return
        api(self.setup.port, "/free", {"unload_models": True, "free_memory": True})
        deadline = time.monotonic() + FREE_TIMEOUT_SECONDS
        while gpu_free_mib(self.setup.gpu) < INTERPOLATION_MIB:
            if time.monotonic() > deadline:
                raise TimeoutError(
                    f"the GPU did not free {INTERPOLATION_MIB} MiB for the interpolation within "
                    f"{FREE_TIMEOUT_SECONDS} s"
                )
            time.sleep(POLL_SECONDS)

    def work_files(self) -> dict[Path, int]:
        """Return every file in the server's input, output and temp folders with its mtime."""
        return {
            path: path.stat().st_mtime_ns
            for folder in WORK_FOLDERS
            for path in self.setup.io_dirs[folder].rglob("*")
            if path.is_file()
        }

    def run(self, graph: dict) -> tuple[dict, float, int]:
        """Submit a graph and wait for it to finish.

        Returns:
            (its history entry, wall seconds from submission to the finished entry, highest GPU
            memory in MiB sampled with nvidia-smi while it ran).

        Raises:
            RuntimeError: If the graph is rejected or fails.
        """
        peak_mib = gpu_used_mib(self.setup.gpu)
        start = time.perf_counter()
        prompt_id = api(self.setup.port, "/prompt", {"prompt": graph})["prompt_id"]
        while prompt_id not in (history := api(self.setup.port, f"/history/{prompt_id}")):
            peak_mib = max(peak_mib, gpu_used_mib(self.setup.gpu))
            time.sleep(POLL_SECONDS)
        seconds = time.perf_counter() - start
        entry = history[prompt_id]
        if entry["status"]["status_str"] != "success":
            raise RuntimeError(f"ComfyUI render failed: {entry['status']['messages']}")
        return entry, seconds, peak_mib

    @contextmanager
    def photo_copy(self, source: Path, image: str) -> Iterator[None]:
        """Place a copy of ``source`` in the server's input folder as ``image`` for one graph.

        On exit, also after an error, every file added or changed in the server's input, output
        and temp folders since entry goes to the trash.
        """
        before = self.work_files()
        shutil.copyfile(source, self.setup.io_dirs["input"] / image)
        try:
            yield
        finally:
            trash([path for path, mtime in self.work_files().items() if before.get(path) != mtime])

    def render(
        self,
        source: Path,
        clip: Path,
        variant: str,
        values: dict[str, object],
        settings: dict[str, object],
        target_frames: int = FRAMES,
    ) -> ClipResult:
        """Render one photo into one 30 fps clip, restoring a finished clip with equal settings.

        A checkpoint restores only when model, revision, settings and source fingerprint match and
        the clip probes as ``target_frames`` frames at FPS; any other clip is rendered again.

        Args:
            source: Working copy to animate.
            clip: Destination ``.mp4``; the sidecar and checkpoint are written beside it.
            variant: Variant name recorded in the sidecar.
            values: Workflow markers and their values, for example ``{"{{PROMPT}}": "..."}``.
                The module sets ``{{IMAGE}}`` and ``{{FILENAME_PREFIX}}`` itself.
            settings: Model settings recorded in the sidecar, for example steps and cfg.
            target_frames: Frames of the interpolated clip at FPS, FRAMES (10 s) by default.

        Returns:
            The clip's provenance and measurements, also saved as sidecar and checkpoint.

        Raises:
            RuntimeError: If the graph fails, the rendered rate differs from the setup's
                native_fps, the native clip is too short for target_frames at FPS, or the
                interpolated clip does not hold target_frames frames at FPS.
            TimeoutError: If the GPU does not free enough memory for the interpolation.
            subprocess.CalledProcessError: If the interpolation worker fails.
        """
        expected = clip_settings(self.setup, values, settings, source, target_frames)
        finished = load_result(clip)
        if finished is not None and restore_matches(finished, self.setup, expected):
            try:
                _, _, frames, fps = probe_clip(clip)
                problem = (
                    None
                    if frames == target_frames and abs(fps - FPS) <= 0.01
                    else f"{frames} frames at {fps:g} fps"
                )
            except Exception as error:  # noqa: BLE001 - any decoder failure re-renders
                problem = str(error)
            if problem is None:
                return finished
            logger.warning(
                f"{clip}: the checkpoint matched but the clip failed the probe "
                f"({problem}); rendering again"
            )
        image = f"{clip.stem}{source.suffix}"
        graph = fill(
            json.loads(self.setup.graph.read_text()),
            {**values, "{{IMAGE}}": image, "{{FILENAME_PREFIX}}": clip.stem},
        )
        with self.photo_copy(source, image):
            entry, seconds, peak_mib = self.run(graph)
            saved = saved_video(entry)
            native = self.setup.io_dirs["temp"] / f"{clip.stem}-native.mp4"
            output = self.setup.io_dirs["output"]
            shutil.move(output / saved["subfolder"] / saved["filename"], native)
            _, _, frames, native_fps = probe_clip(native)
            if abs(native_fps - self.setup.native_fps) > 0.01:
                raise RuntimeError(
                    f"the graph rendered {native_fps:g} fps but the setup records "
                    f"{self.setup.native_fps:g} fps"
                )
            if (frames - 1) / native_fps < (target_frames - 1) / FPS:
                raise RuntimeError(
                    f"the graph rendered {frames} frames at {native_fps:g} fps, too short "
                    f"for {target_frames} frames at {FPS} fps"
                )
            clip.parent.mkdir(parents=True, exist_ok=True)
            trash([clip, clip.with_suffix(".md")])
            self.free_gpu()
            interpolate(native, clip, self.setup.gpu, target_frames)
        width, height, frames, fps = probe_clip(clip)
        if frames != target_frames or abs(fps - FPS) > 0.01:
            raise RuntimeError(
                f"the interpolated clip has {frames} frames at {fps:g} fps, expected "
                f"{target_frames} frames at {FPS} fps"
            )
        result = ClipResult(
            clip=project_relative(clip),
            source=project_relative(source),
            driving="",
            model=self.setup.model,
            revision=self.setup.revision,
            variant=variant,
            settings=expected,
            gpu=self.stats["devices"][0]["name"],
            seconds=round(seconds, 2),
            peak_vram_gb=round((peak_mib - self.baseline_mib) * MIB / BYTES_PER_GB, 3),
            width=width,
            height=height,
            frames=frames,
            fps=fps,
            time_scope="POST /prompt to the finished history entry: model load, sampling, VAE "
            "decode and H.264 encode",
            vram_scope="nvidia-smi memory.used of the pinned GPU sampled during the render, "
            "minus the memory in use before the server started",
        )
        save_result(result, clip)
        return result
