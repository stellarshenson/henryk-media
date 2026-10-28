"""One ComfyUI server on one pinned GPU, and the request cycle the bench reuses.

The server starts on construction and stops on ``stop`` or process exit, so a failed notebook run
does not leave it holding the GPU. Every graph runs through ``run``, which returns the history
entry, the wall seconds and the highest GPU memory sampled while it ran.
"""

import atexit
from collections.abc import Iterator
from contextlib import contextmanager
import json
from pathlib import Path
import re
import subprocess
import time

from henryk_media.animation.advanced_liveportrait import WORK_FOLDERS, trash
from henryk_media.animation.image_to_video import api, fill, gpu_used_mib, port_answers
from henryk_media.imaging.setup import Setup

START_TIMEOUT_SECONDS = 240
STOP_TIMEOUT_SECONDS = 120
RUN_TIMEOUT_SECONDS = 3600
POLL_SECONDS = 1.0
MIB = 2**20
BYTES_PER_GB = 1e9


def saved_image(entry: dict) -> dict:
    """Return the history record of the last PNG a finished graph saved.

    Raises:
        RuntimeError: If the graph saved no PNG.
    """
    files = [
        item
        for output in entry["outputs"].values()
        for item in output.get("images", [])
        if item["filename"].endswith(".png")
    ]
    if not files:
        raise RuntimeError(f"the graph saved no PNG; outputs: {entry['outputs']}")
    return files[-1]


def out_of_memory(error: Exception) -> bool:
    """Return True when a failed graph reports that it ran out of GPU memory."""
    text = str(error).lower()
    return any(
        marker in text for marker in ("out of memory", "outofmemory", "allocation on device")
    )


class ComfyServer:
    """A ComfyUI server on one setup's GPU.

    Args:
        setup: The server, graphs and model descriptions to run.

    Raises:
        RuntimeError: If a server already answers on the setup's port.
        TimeoutError: If the server does not answer within START_TIMEOUT_SECONDS.
    """

    def __init__(self, setup: Setup) -> None:
        if port_answers(setup.port):
            raise RuntimeError(f"a server already answers on port {setup.port}; stop it first")
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

    def model_names(self) -> set[str]:
        """Return every file name the server currently lists for each loader folder."""
        names: set[str] = set()
        for endpoint in (
            "/object_info/UNETLoader",
            "/object_info/UpscaleModelLoader",
            "/object_info/ModelPatchLoader",
            "/object_info/CLIPLoader",
        ):
            try:
                info = api(self.setup.port, endpoint)
            except RuntimeError:
                continue
            for node in info.values():
                for value in (node.get("input", {}).get("required", {}) or {}).values():
                    if isinstance(value, list) and value and isinstance(value[0], list):
                        names.update(str(name) for name in value[0])
        return names

    def work_files(self) -> dict[Path, int]:
        """Return every file in the server's input, output and temp folders with its mtime."""
        return {
            path: path.stat().st_mtime_ns
            for folder in WORK_FOLDERS
            for path in self.setup.io_dirs[folder].rglob("*")
            if path.is_file()
        }

    @contextmanager
    def scratch(self) -> Iterator[None]:
        """Trash every file added or changed in the server's work folders, also after an error."""
        before = self.work_files()
        try:
            yield
        finally:
            trash([path for path, mtime in self.work_files().items() if before.get(path) != mtime])

    def run(self, graph: dict) -> tuple[dict, float, int]:
        """Submit a graph and wait for it to finish.

        Returns:
            (its history entry, wall seconds from submission to the finished entry, highest GPU
            memory in MiB sampled with nvidia-smi while it ran).

        Raises:
            RuntimeError: If the graph is rejected or fails.
            TimeoutError: If the graph does not finish within RUN_TIMEOUT_SECONDS.
        """
        peak_mib = gpu_used_mib(self.setup.gpu)
        start = time.perf_counter()
        prompt_id = api(self.setup.port, "/prompt", {"prompt": graph})["prompt_id"]
        deadline = time.monotonic() + RUN_TIMEOUT_SECONDS
        while prompt_id not in (history := api(self.setup.port, f"/history/{prompt_id}")):
            if time.monotonic() > deadline:
                raise TimeoutError(f"the graph did not finish within {RUN_TIMEOUT_SECONDS} s")
            peak_mib = max(peak_mib, gpu_used_mib(self.setup.gpu))
            time.sleep(POLL_SECONDS)
        seconds = time.perf_counter() - start
        entry = history[prompt_id]
        if entry["status"]["status_str"] != "success":
            raise RuntimeError(f"ComfyUI graph failed: {entry['status']['messages']}")
        return entry, seconds, peak_mib

    def graph(self, name: str, markers: dict[str, object]) -> dict:
        """Return the named graph with every marker replaced by its value."""
        text = (self.setup.graphs[name]).read_text()
        return fill(json.loads(text), markers)

    def saved(self, entry: dict) -> Path:
        """Return the path of the PNG a finished graph saved in the server's output folder."""
        item = saved_image(entry)
        return self.setup.io_dirs["output"] / item["subfolder"] / item["filename"]

    def peak_gb(self, peak_mib: int) -> float:
        """Return the memory above the idle baseline in GB, from a sampled MiB peak."""
        return round((peak_mib - self.baseline_mib) * MIB / BYTES_PER_GB, 3)
