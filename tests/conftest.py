"""Fakes and fixtures of the studio tests; none is autouse, so the other tests are untouched.

No fixture starts ComfyUI, touches a GPU or reads a real photo: the images are synthetic Pillow
images under ``tmp_path`` and nvidia-smi is the FAKE_SMI text.
"""

from dataclasses import replace
from http.server import ThreadingHTTPServer
import json
from pathlib import Path
import threading
import time
import urllib.error
import urllib.request

import numpy as np
from PIL import Image
import pytest

from henryk_media.animation import image_to_video as i2v
from henryk_media.studio.app import Studio
from henryk_media.studio.comfy import StudioServer
from henryk_media.studio.gpus import parse
from henryk_media.studio.web import handler

FAKE_SMI = (
    "0, GPU-00000000-0000-4000-8000-000000000000, NVIDIA RTX PRO 4000 Blackwell, 24467, 24015, 0\n"
    "1, GPU-11111111-1111-4111-8111-111111111111, NVIDIA RTX PRO 6000 Blackwell Max-Q Workstation "
    "Edition, 97887, 96000, 1100\n"
    "2, GPU-22222222-2222-4222-8222-222222222222, NVIDIA RTX PRO 5000 72GB Blackwell, 73415, "
    "72000, 900\n"
)
SAMPLER_TYPES = {"10": "KSampler", "11": "SamplerCustomAdvanced", "12": "VAEDecode"}
OUTPAINT = {  # a valid outpaint job body for the portrait IMG_0001
    "kind": "outpaint",
    "ref": "0/IMG_0001.jpg",
    "aspect": "16x9",
    "width": 1280,
    "prompt": "extend the room",
    "negative_prompt": "person",
    "cfg": 1.0,
}
VIDEO = {  # a valid video job body for the portrait IMG_0001
    "kind": "video",
    "ref": "0/IMG_0001.jpg",
    "prompt": "he smiles",
    "duration": 10,
    "resolution": "1024x768",
    "seed": 42,
}


def noise(size: tuple[int, int], seed: int = 0) -> Image.Image:
    """Return an RGB noise image."""
    pixels = np.random.default_rng(seed).integers(0, 256, (size[1], size[0], 3), dtype=np.uint8)
    return Image.fromarray(pixels, "RGB")


@pytest.fixture
def image_tree(tmp_path: Path) -> Path:
    """A project-like data tree of synthetic images, one link out of it and one prompt file."""
    root = tmp_path / "tree"
    files = {
        "data/raw/IMG_0001.jpg": (600, 800),
        "data/raw/WIDE_0002.jpg": (1600, 900),
        "data/raw/.hidden.png": (60, 80),
        "data/external/camp/images/IMG_0003.png": (600, 800),
        "data/processed/camp/extended/4x3/IMG_0001.png": (1280, 960),
        "outside/secret.png": (60, 80),
    }
    for seed, (name, size) in enumerate(files.items()):
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        noise(size, seed).save(path)
    (root / "data/raw/escape.png").symlink_to(root / "outside/secret.png")
    prompts = root / "data/external/camp/prompts/image-to-video-h3.md"
    prompts.parent.mkdir(parents=True)
    prompts.write_text(
        "# Image-to-video with MiniMax H3\n\n"
        "## IMG_0001\n\nSource: `x.md`\n\n```\nhe smiles and turns his head slowly\n```\n\n"
        "## IMG_0003\n\n```\nshe waves\n```\n"
    )
    return root


def input_roots(tree: Path) -> list[Path]:
    """Return the input roots of an image tree, in the CLI's default order."""
    return [
        tree / "data/raw",
        tree / "data/external/camp/images",
        tree / "data/processed/camp/extended",
    ]


@pytest.fixture
def trashed(monkeypatch: pytest.MonkeyPatch) -> list[Path]:
    """Record every path given to ``trash``; no trash-put runs."""
    from henryk_media.imaging import extender, server
    from henryk_media.studio import app

    paths: list[Path] = []
    for module in (app, server, extender, i2v):
        monkeypatch.setattr(module, "trash", lambda items: paths.extend(items))
    return paths


@pytest.fixture
def fake_film(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> list[tuple]:
    """FILM and the clip probe without a GPU: native 242 frames at 24 fps, clip as interpolated."""
    calls: list[tuple] = []
    weight = tmp_path / "film_net_fp16.safetensors"
    weight.write_bytes(b"weights")
    monkeypatch.setattr(i2v, "FRAME_INTERPOLATION_WEIGHT", weight)

    def interpolate(native: Path, clip: Path, gpu: str, target_frames: int) -> None:
        calls.append((native, clip, gpu, target_frames))
        clip.write_bytes(b"clip")

    def probe(path: Path) -> tuple[int, int, int, float]:
        if path.name.endswith("-native.mp4"):
            return 1024, 768, 242, 24.0
        return 1024, 768, calls[-1][3], 30.0

    monkeypatch.setattr(i2v, "interpolate", interpolate)
    monkeypatch.setattr(i2v, "probe_clip", probe)
    return calls


class FakeServer(StudioServer):
    """A StudioServer without a process: records the launch, emits scripted events, writes noise.

    Class attributes set by the ``fake_server`` fixture: ``io_root`` for the work folders,
    ``instances`` for every server built, ``events`` sent through ``on_event`` on every run and
    ``errors`` raised by the next runs.
    """

    io_root: Path
    instances: list["FakeServer"]
    events: list[dict]
    errors: list[Exception]

    def __init__(self, setup, on_event) -> None:
        self.launched = setup
        self.on_event = on_event
        self.node_types = {}
        self.setup = replace(
            setup, io_dirs={name: self.io_root / name for name in ("input", "output", "temp")}
        )
        for folder in self.setup.io_dirs.values():
            folder.mkdir(parents=True, exist_ok=True)
        self.stats = {"devices": [{"name": "cuda:0 Fake GPU"}]}
        self.baseline_mib = 500
        self.graphs: list[dict] = []
        self.interrupts = 0
        self.stopped = 0
        self.instances.append(self)

    def run(self, graph: dict) -> tuple[dict, float, int]:
        self.node_types = {key: node["class_type"] for key, node in graph.items()}
        self.graphs.append(graph)
        for event in self.events:
            self.on_event(event)
        if self.errors:
            raise self.errors.pop(0)
        save = next(
            (key, node)
            for key, node in graph.items()
            if node["class_type"] in ("SaveImage", "SaveVideo")
        )
        prefix = save[1]["inputs"]["filename_prefix"]
        if save[1]["class_type"] == "SaveVideo":
            name = f"{prefix}_00001_.mp4"
            (self.setup.io_dirs["output"] / name).write_bytes(b"native")
        else:
            name = f"{prefix}_00001_.png"
            noise((64, 48), len(self.graphs)).save(self.setup.io_dirs["output"] / name)
        entry = {"outputs": {save[0]: {"images": [{"filename": name, "subfolder": ""}]}}}
        return entry, 1.5, 1500

    def interrupt(self) -> None:
        self.interrupts += 1

    def stop(self) -> None:
        self.stopped += 1

    def free_gpu(self) -> None:
        pass


@pytest.fixture
def fake_server(tmp_path: Path) -> type[FakeServer]:
    """A FakeServer class whose work folders lie under tmp_path."""
    return type(
        "Fake",
        (FakeServer,),
        {"io_root": tmp_path / "comfy-io", "instances": [], "events": [], "errors": []},
    )


class FakeGate:
    """The person gate with scripted verdicts: the first ``fail`` checks find a stranger."""

    def __init__(self, fail: int = 0) -> None:
        self.fail = fail
        self.checks = 0

    def signatures(self) -> dict[str, str]:
        return {"face": "fake face", "person": "fake person"}

    def check(self, frame: Image.Image, photo_left: int, photo_width: int) -> dict:
        self.checks += 1
        stranger = {
            "detector": "person",
            "label": "person",
            "confidence": 0.9,
            "box": [1.0, 2.0, 30.0, 60.0],
            "inside": 1.0,
            "kind": "stranger",
        }
        violations = [stranger] if self.checks <= self.fail else []
        return {
            "passed": not violations,
            "panels": [[0, photo_left], [photo_left + photo_width, frame.width]],
            "rule": "fake rule",
            "violations": violations,
            "continuations": [],
            "clipped": [],
        }


class FakeGenerator:
    """A generator that sends events through the server, can block, and writes a PNG result."""

    def __init__(self, events: tuple[dict, ...] = (), block: bool = False) -> None:
        self.events = events
        self.release = threading.Event()
        self.started = threading.Event()
        self.jobs: list[str] = []
        if not block:
            self.release.set()

    def run(self, job, server, folder: Path) -> Path:
        self.jobs.append(job.id)
        server.node_types = dict(SAMPLER_TYPES)
        self.started.set()
        for event in self.events:
            server.on_event(event)
        assert self.release.wait(10)
        result = folder / f"{Path(job.path).stem}.png"
        noise((32, 24)).save(result)
        result.with_suffix(".md").write_text(f"# {result.name}\n\n- Fake generator\n")
        return result


def fake_gpus(text: str = FAKE_SMI):
    """Return a ``gpus`` callable over fixed nvidia-smi text."""
    return lambda: parse(text)


@pytest.fixture
def make_studio(
    tmp_path: Path, image_tree: Path, fake_server: type[FakeServer], trashed: list[Path]
):
    """Build Studios over the image tree with fakes; every one is closed on teardown."""
    made: list[Studio] = []

    def make(generators: dict | None = None, **options) -> Studio:
        options.setdefault("server_factory", fake_server)
        options.setdefault("gpus", fake_gpus())
        options.setdefault("external", image_tree / "data/external")
        studio = Studio(
            tmp_path / "state",
            input_roots(image_tree),
            generators or {"outpaint": FakeGenerator(), "video": FakeGenerator()},
            **options,
        )
        made.append(studio)
        return studio

    yield make
    for studio in made:
        studio.close()


class Client:
    """JSON calls against one served studio."""

    def __init__(self, url: str) -> None:
        self.url = url

    def call(
        self, method: str, path: str, data: bytes | None = None, content_type: str | None = None
    ) -> tuple[int, dict | bytes]:
        request = urllib.request.Request(self.url + path, data=data, method=method)
        if content_type:
            request.add_header("Content-Type", content_type)
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                status, body, kind = response.status, response.read(), response.headers
        except urllib.error.HTTPError as error:
            status, body, kind = error.code, error.read(), error.headers
        return status, json.loads(body) if "json" in kind["Content-Type"] else body

    def get(self, path: str) -> tuple[int, dict | bytes]:
        return self.call("GET", path)

    def post(self, path: str, body: dict) -> tuple[int, dict]:
        return self.call("POST", path, json.dumps(body).encode(), "application/json")

    def job(self, job_id: str) -> dict:
        return self.get(f"/api/jobs/{job_id}")[1]["job"]

    def wait(self, job_id: str, *states: str, timeout: float = 10.0) -> dict:
        """Poll the job until it reaches one of the states."""
        deadline = time.monotonic() + timeout
        while (job := self.job(job_id))["state"] not in states:
            assert time.monotonic() < deadline, f"job stuck in {job['state']}: {job}"
            time.sleep(0.02)
        return job


@pytest.fixture
def serve():
    """Serve studios on ephemeral loopback ports; every server stops on teardown."""
    servers: list[ThreadingHTTPServer] = []

    def start(studio: Studio) -> Client:
        server = ThreadingHTTPServer(("127.0.0.1", 0), handler(studio))
        threading.Thread(target=server.serve_forever, args=(0.05,), daemon=True).start()
        servers.append(server)
        return Client(f"http://127.0.0.1:{server.server_address[1]}")

    yield start
    for server in servers:
        server.shutdown()
        server.server_close()
