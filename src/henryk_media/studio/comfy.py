"""The studio's one ComfyUI server, pinned by UUID to the chosen GPU, and its progress events.

``StudioServer`` is ``ComfyServer`` for starting, stopping, running graphs and the outpaint, plus
``image_to_video.Server`` for the clip render and FILM; MRO StudioServer, ComfyServer, Server. A
daemon thread reads ComfyUI's websocket and hands every text message to ``on_event``; prompts are
queued with the listener's client id, so ComfyUI sends all their events to that socket, including
executing and execution_success. ``advance`` turns one message into the job's stage, step and
percent.
"""

from collections.abc import Callable
from dataclasses import dataclass
import json
from pathlib import Path
import shlex
import socket
import threading
from typing import TYPE_CHECKING
import uuid

import websocket

from henryk_media.animation import image_to_video as i2v
from henryk_media.animation.advanced_liveportrait import COMFYUI_DIR
from henryk_media.config import MODELS_DIR, PROJ_ROOT
from henryk_media.imaging.server import ComfyServer
from henryk_media.imaging.setup import Setup
from henryk_media.studio.generators import H3_MODEL, H3_NATIVE_FPS, H3_REVISION

if TYPE_CHECKING:
    from henryk_media.studio.app import Job

IO_ROOT = MODELS_DIR / "photo-animation" / "ComfyUI-studio-io"
IO_FOLDERS = ("input", "output", "temp", "user", "previews")
SERVER_LOG = PROJ_ROOT / "logs" / "studio-comfyui.log"
H3_GRAPH = Path(__file__).with_name("graphs") / "minimax_h3.json"
GRAPHS = {
    "flux3_klein": Path(__file__).parents[1] / "imaging" / "graphs" / "flux3_klein.json",
    "minimax_h3": H3_GRAPH,
}
SAMPLERS = {"KSampler", "SamplerCustomAdvanced"}
RECONNECT_SECONDS = 1.0


@dataclass(frozen=True)
class StudioSetup(Setup):
    """``imaging.setup.Setup`` plus the fields ``image_to_video.Server.render`` reads."""

    model: str
    revision: str
    native_fps: float
    graph: Path


def free_port() -> int:
    """Return a loopback port that was free a moment ago."""
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def comfy_setup(gpu_uuid: str, port: int) -> StudioSetup:
    """Return the setup of a ComfyUI server on 127.0.0.1:port that sees only ``gpu_uuid``."""
    io = {name: IO_ROOT / name for name in IO_FOLDERS}
    q = shlex.quote
    folders = " ".join(f"--{name}-directory {q(str(io[name]))}" for name in IO_FOLDERS)
    return StudioSetup(
        gpu=gpu_uuid,
        port=port,
        launch_command=(
            f"cd {q(str(COMFYUI_DIR))} && CUDA_DEVICE_ORDER=PCI_BUS_ID "
            f"CUDA_VISIBLE_DEVICES={q(gpu_uuid)} HF_HUB_OFFLINE=1 YOLO_OFFLINE=1 MPLBACKEND=Agg "
            f".venv/bin/python main.py --listen 127.0.0.1 --port {port} "
            "--disable-auto-launch --offline --disable-product-tips "
            f"--feature-flag enable_telemetry=false {folders} "
            f"> {q(str(SERVER_LOG))} 2>&1 < /dev/null &"
        ),
        # the trailing space keeps port 8189 from matching 81890
        stop_command=(
            f"kill \"$(pgrep -f '^\\.venv/bin/python main.py --listen 127.0.0.1 --port {port} ')\""
        ),
        io_dirs={name: io[name] for name in ("input", "output", "temp")},
        graphs=dict(GRAPHS),
        paths={},
        model=H3_MODEL,
        revision=H3_REVISION,
        native_fps=H3_NATIVE_FPS,
        graph=H3_GRAPH,
    )


class StudioServer(ComfyServer, i2v.Server):
    """One ComfyUI process for both job kinds, with a websocket listener for its events.

    Args:
        setup: The server from ``comfy_setup``.
        on_event: Called with every JSON message the server sends, on the listener thread.
    """

    def __init__(self, setup: StudioSetup, on_event: Callable[[dict], None]) -> None:
        for name in IO_FOLDERS:
            (setup.io_dirs["input"].parent / name).mkdir(parents=True, exist_ok=True)
        SERVER_LOG.parent.mkdir(parents=True, exist_ok=True)
        self.on_event = on_event
        self.node_types: dict[str, str] = {}
        self.closed = threading.Event()
        super().__init__(setup)
        self.client_id = uuid.uuid4().hex
        url = f"ws://127.0.0.1:{setup.port}/ws?clientId={self.client_id}"
        threading.Thread(target=self.listen, args=(url,), daemon=True).start()

    def listen(self, url: str) -> None:
        """Hand every text frame to ``on_event``, reconnecting after an error until ``stop``."""
        while not self.closed.is_set():
            try:
                connection = websocket.create_connection(url, timeout=1)
            except Exception:  # noqa: BLE001 - the server may still be starting or stopping
                self.closed.wait(RECONNECT_SECONDS)
                continue
            try:
                while not self.closed.is_set():
                    try:
                        frame = connection.recv()
                    except websocket.WebSocketTimeoutException:
                        continue
                    if isinstance(frame, str):  # binary frames are preview images
                        self.on_event(json.loads(frame))
            except Exception:  # noqa: BLE001 - a dropped socket reconnects
                self.closed.wait(RECONNECT_SECONDS)
            finally:
                connection.close()

    def run(self, graph: dict) -> tuple[dict, float, int]:
        """Record each node's class for ``advance``, then run the graph."""
        self.node_types = {key: node["class_type"] for key, node in graph.items()}
        return super().run(graph, client_id=self.client_id)

    def interrupt(self) -> None:
        """Interrupt the graph the server is executing."""
        i2v.api(self.setup.port, "/interrupt", {})

    def release_models(self) -> None:
        """Unload the server's models, so a pipeline keeps one model resident at a time."""
        i2v.api(self.setup.port, "/free", {"unload_models": True, "free_memory": True})

    def stop(self) -> None:
        """Stop the listener, then the server."""
        self.closed.set()
        super().stop()


def advance(job: "Job", message: dict, node_types: dict[str, str]) -> None:
    """Move the job's stage, step and percent forward for one ComfyUI message."""
    kind, data = message.get("type"), message.get("data") or {}
    node = data.get("node")
    if kind == "execution_start":
        job.sampler_seen = False
        job.stage, job.percent = "loading model", 5
    elif kind == "executing" and node is not None:
        if node_types.get(node) in SAMPLERS:
            job.sampler_seen = True
            job.stage, job.percent = "sampling", 10
        elif job.sampler_seen:
            job.stage, job.percent = "decoding", 90
        else:
            job.stage, job.percent = "loading model", 5
    elif kind == "progress" and node_types.get(node) in SAMPLERS:
        job.stage, job.step, job.steps = "sampling", data["value"], data["max"]
        job.percent = round(10 + 78 * data["value"] / data["max"], 1)
    elif kind == "execution_success":
        job.stage, job.percent = ("interpolating", 93) if job.kind == "video" else ("decoding", 90)
