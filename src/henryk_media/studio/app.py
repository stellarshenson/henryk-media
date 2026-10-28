"""The studio core: GPU selection, the image roots, uploads, prompts and the job queue.

One ``threading.Condition`` guards the jobs, the queue, the selected GPU and the one ComfyUI
server. One worker thread runs the jobs in submission order; on every WAIT_SECONDS wait without a
job it calls ``tick``, which stops a server idle for IDLE_SECONDS. A job's record is written to
``<state>/jobs/<id>/job.json`` at every state change; progress lives in memory. Nothing is written
outside the state folder and the ComfyUI work folders.
"""

from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime
import io
import json
import os
from pathlib import Path
import re
import secrets
import threading
import time

from PIL import Image

from henryk_media.animation.advanced_liveportrait import trash
from henryk_media.config import EXTERNAL_DATA_DIR, PROCESSED_DATA_DIR, RAW_DATA_DIR
from henryk_media.imaging.composite import Geometry
from henryk_media.imaging.extender import ASPECTS, FEATHER
from henryk_media.imaging.server import out_of_memory
from henryk_media.studio import prompts
from henryk_media.studio.comfy import StudioServer, advance, comfy_setup, free_port
from henryk_media.studio.generators import DURATIONS, SIZES, Generator, oriented_size
from henryk_media.studio.gpus import Gpu, gb, list_gpus, need_gb

SUFFIXES = {".png", ".jpg", ".jpeg", ".webp", ".mp4", ".md"}  # files /api/file serves
IMAGE_SUFFIXES = {".png", ".jpg", ".jpeg", ".webp"}
UPLOAD_FORMATS = {"JPEG": ".jpg", "PNG": ".png", "WEBP": ".webp"}
UPLOAD_LIMIT = 50_000_000
WIDTHS = (1024, 1280, 1536, 1920)
KINDS = ("outpaint", "video")
TERMINAL = ("done", "failed", "cancelled")
IDLE_SECONDS = 900
WAIT_SECONDS = 5
INTERRUPTED = "interrupted by a studio restart"


class ApiError(Exception):
    """A refused request: the HTTP status and the message the page shows."""

    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status


class Cancelled(Exception):
    """A running job's cancel took effect before its generator started."""


@dataclass
class Job:
    """One job record; ``path`` is the resolved source, ``result`` and ``sidecar`` file names."""

    id: str
    kind: str
    path: str
    label: str
    gpu: dict
    params: dict
    created: str
    state: str = "queued"
    stage: str = "queued"
    step: int | None = None
    steps: int | None = None
    percent: float = 0
    error: str | None = None
    started: str | None = None
    finished: str | None = None
    result: str | None = None
    sidecar: str | None = None
    cancel: bool = False
    sampler_seen: bool = False


def now() -> str:
    """Return the local time in ISO-8601 at second precision."""
    return datetime.now().astimezone().isoformat(timespec="seconds")


def default_roots() -> list[Path]:
    """Return the project's input roots: raw photos, campaign images and extended frames."""
    return [
        RAW_DATA_DIR,
        *sorted(EXTERNAL_DATA_DIR.glob("*/images")),
        *sorted(PROCESSED_DATA_DIR.glob("*/extended")),
    ]


def hidden(relative: Path) -> bool:
    """Return True when a path part is hidden or an archive the picker never shows."""
    return any(part.startswith((".", "@archive")) for part in relative.parts)


def describe(kind: str, params: dict) -> str:
    """Return the job's name in a refusal message."""
    if kind == "outpaint":
        return f"FLUX 3 Klein outpaint {params['aspect']} at {params['width']} px"
    return f"MiniMax H3 {params['resolution']} {params['duration']} s"


class Studio:
    """The studio's state and its one worker.

    Args:
        state_dir: Folder for uploads, saved prompts and job folders.
        input_roots: Folders the picker lists, in order.
        generators: The generator per job kind.
        server_factory: Builds the ComfyUI server from a setup and the event callback.
        gpus: Returns the nvidia-smi rows.
        clock: Monotonic seconds for the idle stop.
        external: Folder of the campaigns whose archived H3 prompts become presets.
    """

    def __init__(
        self,
        state_dir: Path,
        input_roots: list[Path],
        generators: dict[str, Generator],
        server_factory=StudioServer,
        gpus=list_gpus,
        clock=time.monotonic,
        external: Path = EXTERNAL_DATA_DIR,
    ) -> None:
        state_dir = Path(state_dir)
        self.uploads, self.jobs_dir, self.prompts_dir = (
            state_dir / name for name in ("uploads", "jobs", "prompts")
        )
        for folder in (self.uploads, self.jobs_dir, self.prompts_dir):
            folder.mkdir(parents=True, exist_ok=True)
        self.roots = [*map(Path, input_roots), self.uploads, self.jobs_dir]
        self.generators = generators
        self.server_factory = server_factory
        self.gpus = gpus
        self.clock = clock
        self.external = external
        self.lock = threading.Condition()
        self.jobs: dict[str, Job] = {}
        self.queue: deque[str] = deque()
        self.selected: Gpu | None = None
        self.server: StudioServer | None = None
        self.running: Job | None = None
        self.closed = False
        self.last_activity = clock()
        self.recover()
        self.worker = threading.Thread(target=self.work, daemon=True)
        self.worker.start()

    # --- files -----------------------------------------------------------------------------

    def entry(self, path: Path) -> dict | None:
        """Return ``{"ref", "label"}`` of a file under a root, or None when no root holds it."""
        resolved = path.resolve()
        for index, root in enumerate(self.roots):
            if resolved.is_relative_to(root.resolve()):
                relative = resolved.relative_to(root.resolve())
                return {
                    "ref": f"{index}/{relative.as_posix()}",
                    "label": f"{root.name}/{relative}",
                }
        return None

    def resolve(self, ref: object) -> Path:
        """Return the file a ref names, or raise 404 for anything outside the roots.

        Raises:
            ApiError: 404 for a malformed ref, a path escaping its root by ``..``, an absolute
                path or a symlink, a hidden part, a missing file or a suffix not served.
        """
        index, _, relative = ref.partition("/") if isinstance(ref, str) else ("", "", "")
        if not (re.fullmatch(r"[0-9]+", index) and int(index) < len(self.roots) and relative):
            raise ApiError(404, "not found")
        root = self.roots[int(index)].resolve()
        path = (root / relative).resolve()
        if (
            not path.is_relative_to(root)
            or hidden(path.relative_to(root))
            or not path.is_file()
            or path.suffix.lower() not in SUFFIXES
        ):
            raise ApiError(404, "not found")
        return path

    def images(self) -> list[dict]:
        """Return every image under the input roots and the uploads, sorted by label."""
        items = []
        for index, root in enumerate(self.roots[:-1]):  # the job folders are not picked
            for path in root.rglob("*"):
                relative = path.relative_to(root)
                if path.suffix.lower() in IMAGE_SUFFIXES and not hidden(relative):
                    try:
                        self.resolve(f"{index}/{relative.as_posix()}")  # drops links out
                    except ApiError:
                        continue
                    items.append(
                        {
                            "ref": f"{index}/{relative.as_posix()}",
                            "label": f"{root.name}/{relative}",
                        }
                    )
        return sorted(items, key=lambda item: item["label"])

    def upload(self, name: str, data: bytes) -> dict:
        """Store a decodable JPEG, PNG or WebP under the uploads and return its entry.

        Raises:
            ApiError: 400 when Pillow cannot decode the bytes as one of the three formats, 409
                when the name already holds a different image.
        """
        try:
            with Image.open(io.BytesIO(data), formats=list(UPLOAD_FORMATS)) as image:
                image.load()
                suffix = UPLOAD_FORMATS[image.format]
        except (OSError, ValueError, Image.DecompressionBombError) as error:
            raise ApiError(400, f"not a JPEG, PNG or WebP image: {error}") from error
        stem = re.sub(r"[^A-Za-z0-9._-]", "", Path(name).stem).lstrip(".")[:100] or "upload"
        path = self.uploads / f"{stem}{suffix}"
        if path.exists() and path.read_bytes() != data:
            raise ApiError(
                409,
                f"uploads/{path.name} already holds another image; rename the file and upload again",
            )
        staged = self.uploads / f".{secrets.token_hex(8)}.tmp"
        staged.write_bytes(data)
        os.replace(staged, path)
        return self.entry(path)

    # --- prompts ---------------------------------------------------------------------------

    def prompts(self, ref: object, kind: object) -> dict:
        """Return the fields last submitted for this image and kind, and the preset."""
        if kind not in KINDS:
            raise ApiError(400, f"unknown kind {kind!r}; use one of {list(KINDS)}")
        path = self.resolve(ref)
        if kind == "outpaint":
            preset = dict(prompts.OUTPAINT_PRESET)
        else:
            text = prompts.production_prompt(path.stem, self.external)
            preset = None if text is None else {"prompt": text}
        return {"saved": prompts.load_saved(self.prompts_dir, kind, path), "preset": preset}

    # --- GPUs ------------------------------------------------------------------------------

    def gpu_list(self) -> dict:
        """Return the nvidia-smi rows in GB and the selected index."""
        rows = self.gpus()
        with self.lock:
            selected = None if self.selected is None else self.selected.index
        return {
            "gpus": [
                {
                    "index": row.index,
                    "uuid": row.uuid,
                    "name": row.name,
                    "total_gb": round(gb(row.total_mib), 1),
                    "free_gb": round(gb(row.free_mib), 1),
                }
                for row in rows
            ],
            "selected": selected,
        }

    def select_gpu(self, index: object) -> dict:
        """Select one GPU; refused while a job waits or runs, stops a server on another GPU."""
        row = next((row for row in self.gpus() if type(index) is int and row.index == index), None)
        if row is None:
            raise ApiError(400, f"no GPU with index {index!r}")
        with self.lock:
            if self.queue or self.running is not None:
                raise ApiError(409, "a job is queued or running; change the GPU when it ends")
            if self.server is not None and self.server.setup.gpu != row.uuid:
                self.stop_server()
            self.selected = row
        return {"selected": row.index}

    # --- jobs ------------------------------------------------------------------------------

    def submit(self, body: dict) -> Job:
        """Validate one job, check that it fits the selected GPU and queue it.

        Raises:
            ApiError: 400 for an invalid field, no GPU, a photo already wide or a recorded peak
                above the GPU total; 404 for the ref; 409 for a peak above the free memory.
        """
        kind = body.get("kind")
        if kind not in KINDS:
            raise ApiError(400, f"unknown kind {kind!r}; use one of {list(KINDS)}")
        with self.lock:
            selected = self.selected
        if selected is None:
            raise ApiError(400, "select a GPU first")
        path = self.resolve(body.get("ref"))
        if path.suffix.lower() not in IMAGE_SUFFIXES:
            raise ApiError(404, "not found")
        prompt = body.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            raise ApiError(400, "the prompt is empty")
        if kind == "outpaint":
            params = self.outpaint_params(body, path)
        else:
            params = self.video_params(body)
        params["prompt"] = prompt
        self.fit(kind, params, selected)

        job = Job(
            id=f"{datetime.now():%Y%m%d-%H%M%S}-{secrets.token_hex(3)}",
            kind=kind,
            path=str(path),
            label=self.entry(path)["label"],
            gpu={
                "index": selected.index,
                "name": selected.name,
                "uuid": selected.uuid,
                "total_gb": round(gb(selected.total_mib), 1),
            },
            params=params,
            created=now(),
        )
        fields = {key: value for key, value in body.items() if key not in ("kind", "ref")}
        prompts.save_submitted(self.prompts_dir, kind, path, fields)
        (self.jobs_dir / job.id).mkdir()
        with self.lock:
            self.jobs[job.id] = job
            self.queue.append(job.id)
            self.write(job)
            self.lock.notify_all()
        return job

    def outpaint_params(self, body: dict, path: Path) -> dict:
        """Return the outpaint settings, refusing an aspect the photo already reaches."""
        aspect, width, cfg = body.get("aspect"), body.get("width", 1280), body.get("cfg", 1.0)
        negative = body.get("negative_prompt", "")
        if aspect not in ASPECTS:
            raise ApiError(400, f"unknown aspect {aspect!r}; use one of {list(ASPECTS)}")
        if width not in WIDTHS or type(width) is not int:
            raise ApiError(400, f"unknown width {width!r}; use one of {list(WIDTHS)}")
        if type(cfg) not in (int, float) or not 0 < cfg <= 100:
            raise ApiError(400, f"cfg must be a number above 0 and at most 100, not {cfg!r}")
        if not isinstance(negative, str):
            raise ApiError(400, "the negative prompt must be text")
        size = oriented_size(path)
        geometry = Geometry.for_aspect(size, ASPECTS[aspect], FEATHER, width)
        if geometry.photo_size(size)[0] >= geometry.width:
            raise ApiError(
                400,
                f"the photo ({size[0]}x{size[1]}) is already as wide as {aspect} or wider; "
                "nothing is left to extend",
            )
        return {"aspect": aspect, "width": width, "negative_prompt": negative, "cfg": float(cfg)}

    def video_params(self, body: dict) -> dict:
        """Return the video settings."""
        duration, resolution, seed = (
            body.get("duration"),
            body.get("resolution"),
            body.get("seed", 42),
        )
        if duration not in DURATIONS or type(duration) is not int:
            raise ApiError(400, f"unknown duration {duration!r}; use one of {list(DURATIONS)}")
        if resolution not in SIZES:
            raise ApiError(400, f"unknown resolution {resolution!r}; use one of {list(SIZES)}")
        if type(seed) is not int or seed < 0:
            raise ApiError(400, f"the seed must be a non-negative integer, not {seed!r}")
        return {"duration": duration, "resolution": resolution, "seed": seed}

    def fit(self, kind: str, params: dict, selected: Gpu) -> None:
        """Refuse a job whose recorded peak exceeds the GPU's total or available memory."""
        row = next((row for row in self.gpus() if row.uuid == selected.uuid), selected)
        need = need_gb(kind, params)
        name = (
            f"{describe(kind, params)} needs {need} GB (recorded peak); GPU {row.index} {row.name}"
        )
        if need > gb(row.total_mib):
            raise ApiError(400, f"{name} has {gb(row.total_mib):.1f} GB in total")
        with self.lock:
            server = self.server
        available = row.free_mib
        if server is not None and server.setup.gpu == row.uuid:
            available += row.used_mib - server.baseline_mib  # the studio's own models
        if need > gb(available):
            raise ApiError(409, f"{name} has {gb(available):.1f} GB available")

    def job(self, job_id: str) -> Job:
        """Return one job record, or raise 404."""
        with self.lock:
            if job_id not in self.jobs:
                raise ApiError(404, "no such job")
            return self.jobs[job_id]

    def view(self, job: Job) -> dict:
        """Return the job as the API shows it, with refs for the source and the result."""
        record = asdict(job)
        for key in ("path", "label", "cancel", "sampler_seen"):
            del record[key]
        folder = self.jobs_dir / job.id
        record["source"] = self.entry(Path(job.path)) or {"ref": None, "label": job.label}
        if job.result is not None:
            record["result"] = self.entry(folder / job.result)
            record["sidecar"] = {"ref": self.entry(folder / job.sidecar)["ref"]}
        return record

    def job_list(self) -> list[dict]:
        """Return every job, newest first."""
        with self.lock:
            return [self.view(job) for job in reversed(self.jobs.values())]

    def cancel(self, job_id: str) -> Job:
        """Cancel a queued job, or interrupt a running one; 409 for a finished job."""
        with self.lock:
            job = self.job(job_id)
            if job.state == "queued":
                self.queue.remove(job.id)
                self.finish(job, "cancelled")
                return job
            if job.state != "running":
                raise ApiError(409, f"the job is already {job.state}")
            job.cancel = True
            server = self.server
        if server is not None:
            server.interrupt()
        return job

    def write(self, job: Job) -> None:
        """Write the job's record atomically."""
        path = self.jobs_dir / job.id / "job.json"
        staged = path.with_name("job.json.tmp")
        staged.write_text(json.dumps(asdict(job), indent=2))
        os.replace(staged, path)

    def finish(self, job: Job, state: str) -> None:
        """End a job in a terminal state; the caller holds the lock."""
        job.state = job.stage = state
        job.finished = now()
        if state == "done":
            job.percent = 100
        if self.running is job:
            self.running = None
        self.last_activity = self.clock()
        self.write(job)

    def recover(self) -> None:
        """Load the job records on disk; a job that was queued or running ends failed."""
        for record in sorted(self.jobs_dir.glob("*/job.json")):
            job = Job(**json.loads(record.read_text()))
            if job.state not in TERMINAL:
                job.error = INTERRUPTED
                self.finish(job, "failed")
            self.jobs[job.id] = job

    # --- worker ----------------------------------------------------------------------------

    def on_event(self, message: dict) -> None:
        """Advance the running job for one ComfyUI message."""
        with self.lock:
            if self.running is not None and self.server is not None:
                advance(self.running, message, self.server.node_types)

    def work(self) -> None:
        """Run the queued jobs one at a time, in submission order."""
        while True:
            with self.lock:
                while not self.queue and not self.closed:
                    if not self.lock.wait(WAIT_SECONDS):
                        self.tick()
                if self.closed:
                    return
                job = self.jobs[self.queue.popleft()]
                self.running = job
                job.state, job.started = "running", now()
                if self.server is not None and self.server.setup.gpu != job.gpu["uuid"]:
                    self.stop_server()
                job.stage, job.percent = (
                    ("loading model", 5) if self.server is not None else ("starting server", 2)
                )
                self.write(job)
                earlier = [
                    other
                    for other in self.jobs.values()
                    if other.state in TERMINAL
                    and other.kind == job.kind
                    and other.path == job.path
                ]
                for other in earlier:
                    del self.jobs[other.id]
            self.execute(job, [self.jobs_dir / other.id for other in earlier])

    def execute(self, job: Job, earlier: list[Path]) -> None:
        """Trash the earlier results, start the server when none runs, run the generator."""
        try:
            trash(earlier)  # the latest result of a kind and source only
            with self.lock:
                server = self.server
            if server is None:
                server = self.server_factory(
                    comfy_setup(job.gpu["uuid"], free_port()), self.on_event
                )
                with self.lock:
                    self.server = server
                    job.stage, job.percent = "loading model", 5
            if job.cancel:
                raise Cancelled
            result = self.generators[job.kind].run(job, server, self.jobs_dir / job.id)
            sidecar = result.with_suffix(".md")
            with sidecar.open("a") as handle:
                handle.write(
                    f"- Picked file: {job.label}\n"
                    f"- Studio GPU: index {job.gpu['index']}, {job.gpu['name']}, "
                    f"{job.gpu['uuid']}\n"
                )
        except Exception as error:  # noqa: BLE001 - every failure ends the job, not the worker
            with self.lock:
                if job.cancel:
                    self.finish(job, "cancelled")
                    return
                job.error = str(error)
                if out_of_memory(error):
                    job.error = (
                        f"out of memory on GPU {job.gpu['index']} {job.gpu['name']} "
                        f"({job.gpu['total_gb']} GB): {error}"
                    )
                self.finish(job, "failed")
            return
        with self.lock:
            if job.cancel:
                self.finish(job, "cancelled")  # keeps no result
                return
            job.result, job.sidecar = result.name, sidecar.name
            self.finish(job, "done")

    def tick(self) -> None:
        """Stop the server after IDLE_SECONDS without a job."""
        with self.lock:
            if (
                self.server is not None
                and not self.queue
                and self.running is None
                and self.clock() - self.last_activity >= IDLE_SECONDS
            ):
                self.stop_server()

    def stop_server(self) -> None:
        """Stop the server, freeing its GPU memory; the caller holds the lock."""
        server, self.server = self.server, None
        if server is not None:
            server.stop()

    def close(self) -> None:
        """Stop the worker and the server."""
        with self.lock:
            self.closed = True
            self.lock.notify_all()
            self.stop_server()
