"""Tests for the studio jobs: GPU pinning, queue, progress, generators, sidecars and restart."""

from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import re
import threading
from types import SimpleNamespace

from conftest import FAKE_SMI, OUTPAINT, VIDEO, FakeGate, FakeGenerator, fake_gpus
from PIL import Image
import websocket

from henryk_media.config import PROJ_ROOT
from henryk_media.imaging.composite import Geometry, interior_matches
from henryk_media.imaging.extender import ASPECTS, FEATHER
from henryk_media.studio import comfy
from henryk_media.studio.app import INTERRUPTED, Job
from henryk_media.studio.generators import GATE_FAILED, H3_REVISION, Outpaint, Video
from henryk_media.studio.gpus import parse
from henryk_media.studio.prompts import OUTPAINT_NEGATIVE, OUTPAINT_PROMPT

GPU_1 = "GPU-11111111-1111-4111-8111-111111111111"
GPU_2 = "GPU-22222222-2222-4222-8222-222222222222"
RECIPE = PROJ_ROOT / ".agents/skills/image-outpainting/references/extender-recipe.md"


def real(gate: FakeGate | None = None) -> dict:
    """The studio's real generators, with a scripted person gate."""
    return {"outpaint": Outpaint(gate or FakeGate()), "video": Video()}


def submit(client, body: dict) -> dict:
    status, reply = client.post("/api/jobs", body)
    assert status == 201, reply
    return reply["job"]


def test_job_launches_comfyui_pinned_to_the_chosen_gpu_uuid(
    make_studio, serve, fake_server
) -> None:
    client = serve(make_studio())
    job = submit(client, OUTPAINT)
    done = client.wait(job["id"], "done")
    assert done["gpu"]["uuid"] == GPU_1  # the largest card that held the frame
    setup = fake_server.instances[0].launched
    assert setup.gpu == GPU_1
    command = setup.launch_command
    pin = f"CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES={GPU_1} "
    assert pin in command
    assert command.index(pin) < command.index(".venv/bin/python main.py")
    assert f"--port {setup.port} " in command


def test_server_moves_to_the_gpu_the_next_job_chooses(make_studio, serve, fake_server) -> None:
    texts = [FAKE_SMI.replace("97887, 96000, 1100", "97887, 1000, 96887")]  # GPU 1 busy
    client = serve(make_studio(gpus=lambda: parse(texts[0])))
    first = submit(client, OUTPAINT)
    client.wait(first["id"], "done")
    assert fake_server.instances[0].launched.gpu == GPU_2  # the largest card with room
    texts[0] = FAKE_SMI  # GPU 1 frees up
    second = submit(client, OUTPAINT)
    client.wait(second["id"], "done")
    assert fake_server.instances[0].stopped == 1  # the server moves off GPU 2
    assert fake_server.instances[1].launched.gpu == GPU_1
    third = submit(client, OUTPAINT)
    client.wait(third["id"], "done")
    assert len(fake_server.instances) == 2  # same choice as the running server: reused
    assert fake_server.instances[1].stopped == 0


def tree_hashes(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file() and not path.is_symlink()
    }


def test_jobs_leave_the_input_tree_unchanged(
    make_studio, serve, image_tree, fake_film, tmp_path
) -> None:
    before = tree_hashes(image_tree)
    names = sorted(path.name for path in image_tree.rglob("*"))
    client = serve(make_studio(real()))
    outpaint = client.wait(submit(client, OUTPAINT)["id"], "done", "failed")
    video = client.wait(submit(client, VIDEO)["id"], "done", "failed")
    assert (outpaint["state"], video["state"]) == ("done", "done"), (outpaint, video)
    assert tree_hashes(image_tree) == before
    assert sorted(path.name for path in image_tree.rglob("*")) == names
    for job in (outpaint, video):
        assert (
            tmp_path / "state/jobs" / job["id"] / job["result"]["label"].split("/")[-1]
        ).exists()
        assert job["result"]["ref"].startswith("4/")  # the studio's job folder root


def test_outpaint_preset_and_edited_prompts_reach_the_graph(
    make_studio, serve, fake_server
) -> None:
    recipe = RECIPE.read_text()
    assert OUTPAINT_PROMPT == re.search(r"## Prompt\n.*?```\n(.*?)\n```", recipe, re.DOTALL)[1]
    assert f"The negative prompt is `{OUTPAINT_NEGATIVE}`" in recipe
    client = serve(make_studio(real()))
    preset = client.get("/api/prompts?ref=0/IMG_0001.jpg&kind=outpaint")[1]["preset"]
    assert preset == {"prompt": OUTPAINT_PROMPT, "negative_prompt": OUTPAINT_NEGATIVE, "cfg": 1.0}

    edited = {**OUTPAINT, "prompt": "an edited room", "negative_prompt": "an edited negative"}
    client.wait(submit(client, edited)["id"], "done")
    graph = fake_server.instances[0].graphs[0]
    assert graph["7"]["inputs"]["text"] == "an edited room"
    assert graph["8"]["inputs"]["text"] == "an edited negative"


def test_cfg_defaults_to_one_and_reaches_the_graph(make_studio, serve, fake_server) -> None:
    client = serve(make_studio(real()))
    assert client.get("/api/prompts?ref=0/IMG_0001.jpg&kind=outpaint")[1]["preset"]["cfg"] == 1.0
    client.wait(submit(client, {**OUTPAINT, "cfg": 2.5})["id"], "done")
    assert fake_server.instances[0].graphs[0]["10"]["inputs"]["cfg"] == 2.5
    omitted = {key: value for key, value in OUTPAINT.items() if key not in ("cfg", "resolution")}
    default = submit(client, omitted)
    assert (default["params"]["cfg"], default["params"]["size"]) == (1.0, [1920, 1080])
    client.wait(default["id"], "done")
    assert fake_server.instances[0].graphs[-1]["10"]["inputs"]["cfg"] == 1.0
    for cfg in (0, 100.5, "2", True):
        assert client.post("/api/jobs", {**OUTPAINT, "cfg": cfg})[0] == 400, cfg


def test_outpaint_keeps_the_photo_pixels_over_noise(make_studio, serve, tmp_path) -> None:
    client = serve(make_studio(real()))
    job = client.wait(submit(client, OUTPAINT)["id"], "done")
    folder = tmp_path / "state/jobs" / job["id"]
    with Image.open(folder / "input/IMG_0001.png") as opened:
        working = opened.convert("RGB")
    with Image.open(folder / "IMG_0001.png") as opened:
        result = opened.convert("RGB")
    geometry = Geometry.for_aspect(working.size, ASPECTS["16x9"], FEATHER, 1280)
    assert result.size == (1280, 720)
    origin = geometry.origin(working.size)
    assert interior_matches(result, geometry.resized(working), origin, FEATHER)


def test_person_gate_retries_seeds_and_fails_after_six(make_studio, serve, fake_server, tmp_path):
    client = serve(make_studio(real(FakeGate(fail=3))))
    job = client.wait(submit(client, OUTPAINT)["id"], "done", "failed")
    assert job["state"] == "done", job
    seeds = [graph["10"]["inputs"]["seed"] for graph in fake_server.instances[0].graphs]
    assert seeds == [42, 43, 44, 45]
    checkpoint = tmp_path / "state/jobs" / job["id"] / "checkpoints/IMG_0001.json"
    assert json.loads(checkpoint.read_text())["seed"] == 45

    client = serve(make_studio(real(FakeGate(fail=6))))
    job = client.wait(submit(client, {**OUTPAINT, "aspect": "4x3"})["id"], "done", "failed")
    assert (job["state"], job["error"], job["result"]) == ("failed", GATE_FAILED, None)
    assert len(fake_server.instances[-1].graphs) == 6


def test_video_runs_h3_at_the_recorded_settings_then_film(
    make_studio, serve, fake_server, fake_film, tmp_path
) -> None:
    client = serve(make_studio(real()))
    job = client.wait(submit(client, VIDEO)["id"], "done", "failed")
    assert job["state"] == "done", job
    graph = fake_server.instances[0].graphs[0]
    types = {node["class_type"]: node["inputs"] for node in graph.values()}
    assert types["UNETLoader"]["unet_name"] == "minimax_h3_fl2va_pruned_bf16.safetensors"
    assert (types["BasicScheduler"]["steps"], types["BasicScheduler"]["scheduler"]) == (
        20,
        "simple",
    )
    assert types["KSamplerSelect"]["sampler_name"] == "res_multistep"
    assert "BasicGuider" in types and "CFGGuider" not in types
    assert "{{NEGATIVE_PROMPT}}" not in json.dumps(graph)
    inputs = [value for node in graph.values() for value in node["inputs"].values()]
    assert not [value for value in inputs if isinstance(value, str) and "{{" in value]
    checkpoint = json.loads(
        (tmp_path / "state/jobs" / job["id"] / "checkpoints/IMG_0001.json").read_text()
    )
    assert (
        checkpoint["revision"] == H3_REVISION
        and "e5eb578a89295337b8ff433a035929ce0279e0b6" in H3_REVISION
    )
    assert (checkpoint["fps"], checkpoint["frames"]) == (30.0, 300)
    assert fake_film[0][2] == "GPU-11111111-1111-4111-8111-111111111111"
    assert fake_film[0][3] == 300


def test_video_job_uses_exactly_the_submitted_prompt(make_studio, serve, fake_server, fake_film):
    client = serve(make_studio(real()))
    text = "  For the target video,\n\nintegrated_multimodal_description: [Shot 1] edited; \t\n"
    body = {key: value for key, value in VIDEO.items() if key != "seed"}  # the seed defaults to 42
    client.wait(submit(client, {**body, "prompt": text})["id"], "done")
    assert fake_server.instances[0].graphs[0]["6"]["inputs"]["prompt"] == text
    assert fake_server.instances[0].graphs[0]["7"]["inputs"]["noise_seed"] == 42
    assert client.post("/api/jobs", {**VIDEO, "prompt": " \n"})[0] == 400


def test_comfyui_events_advance_stage_and_percent(make_studio, serve, fake_server) -> None:
    generator = FakeGenerator(block=True)
    client = serve(make_studio({"outpaint": generator, "video": generator}))
    job = submit(client, VIDEO)
    assert generator.started.wait(10)
    server = fake_server.instances[0]
    seen = []
    for message in (
        {"type": "execution_start", "data": {}},
        {"type": "executing", "data": {"node": "11"}},
        {"type": "progress", "data": {"node": "11", "value": 3, "max": 20}},
        {"type": "progress", "data": {"node": "12", "value": 1, "max": 1}},  # not a sampler
        {"type": "executing", "data": {"node": "12"}},
        {"type": "executing", "data": {"node": None}},  # ignored
        {"type": "execution_success", "data": {}},
    ):
        server.on_event(message)
        state = client.job(job["id"])
        seen.append((state["stage"], state["step"], state["steps"], state["percent"]))
    assert seen == [
        ("loading model", None, None, 5),
        ("sampling", None, None, 10),
        ("sampling", 3, 20, 21.7),
        ("sampling", 3, 20, 21.7),
        ("decoding", 3, 20, 90),
        ("decoding", 3, 20, 90),
        ("interpolating", 3, 20, 93),
    ]
    generator.release.set()
    done = client.wait(job["id"], "done")
    assert (done["stage"], done["percent"]) == ("done", 100)


def test_listener_hands_text_frames_to_on_event_and_reconnects(monkeypatch) -> None:
    server = object.__new__(comfy.StudioServer)
    server.closed = threading.Event()
    events: list[dict] = []
    server.on_event = events.append
    frames = iter(
        [
            json.dumps({"type": "a"}),
            b"preview image",  # binary frames are skipped
            websocket.WebSocketTimeoutException(),  # an idle second
            ConnectionError("dropped"),  # reconnects
            json.dumps({"type": "b"}),
        ]
    )

    class Connection:
        def recv(self) -> str | bytes:
            item = next(frames, None)
            if item is None:
                server.closed.set()
                raise websocket.WebSocketTimeoutException()
            if isinstance(item, Exception):
                raise item
            return item

        def close(self) -> None:
            pass

    urls: list[str] = []
    monkeypatch.setattr(
        comfy.websocket, "create_connection", lambda url, timeout: urls.append(url) or Connection()
    )
    monkeypatch.setattr(comfy, "RECONNECT_SECONDS", 0)
    server.listen("ws://127.0.0.1:1/ws?clientId=x")
    assert events == [{"type": "a"}, {"type": "b"}]
    assert urls == ["ws://127.0.0.1:1/ws?clientId=x"] * 2


def test_graph_is_queued_with_the_listener_client_id(monkeypatch) -> None:
    server = object.__new__(comfy.StudioServer)
    server.setup = SimpleNamespace(port=1, gpu=GPU_2)
    server.client_id = "listener"
    bodies: list[dict] = []

    def api(port: int, path: str, body: dict | None = None) -> dict:
        if path == "/prompt":
            bodies.append(body)
            return {"prompt_id": "p"}
        return {"p": {"status": {"status_str": "success"}}}

    monkeypatch.setattr("henryk_media.imaging.server.api", api)
    monkeypatch.setattr("henryk_media.imaging.server.gpu_used_mib", lambda gpu: 0)
    server.run({"1": {"class_type": "KSampler"}})
    assert bodies[0]["client_id"] == server.client_id


def test_out_of_memory_fails_with_a_plain_warning(make_studio, serve, fake_server, fake_film):
    fake_server.errors.append(RuntimeError("ComfyUI render failed: torch.OutOfMemoryError"))
    client = serve(make_studio(real()))
    job = client.wait(submit(client, VIDEO)["id"], "done", "failed")
    assert (job["state"], job["stage"], job["result"]) == ("failed", "failed", None)
    assert "needs " in job["error"]
    assert job["error"].endswith("; the workstation cannot provide it")
    for hidden in ("NVIDIA", "GPU", "102.6", "torch.OutOfMemoryError"):
        assert hidden not in job["error"], job["error"]


def test_jobs_run_one_at_a_time_in_submission_order(make_studio, serve) -> None:
    generator = FakeGenerator(block=True)
    client = serve(make_studio({"outpaint": generator, "video": generator}))
    third = {**OUTPAINT, "ref": "1/IMG_0003.png"}  # another source, so no job trashes another
    jobs = [submit(client, OUTPAINT), submit(client, VIDEO), submit(client, third)]
    assert generator.started.wait(10)
    assert [client.job(job["id"])["state"] for job in jobs] == ["running", "queued", "queued"]
    generator.release.set()
    finished = [client.wait(job["id"], "done") for job in jobs]
    assert generator.jobs == [job["id"] for job in jobs]
    assert [job["id"] for job in client.get("/api/jobs")[1]["jobs"]] == [
        job["id"] for job in reversed(jobs)
    ]
    assert finished[0]["finished"] <= finished[1]["started"] <= finished[2]["started"]


def test_cancel_removes_a_queued_job_and_interrupts_a_running_one(
    make_studio, serve, fake_server
) -> None:
    generator = FakeGenerator(block=True)
    client = serve(make_studio({"outpaint": generator, "video": generator}))
    running, queued = submit(client, OUTPAINT), submit(client, VIDEO)
    assert generator.started.wait(10)
    status, body = client.post(f"/api/jobs/{queued['id']}/cancel", {})
    assert (status, body["job"]["state"]) == (200, "cancelled")
    assert client.post(f"/api/jobs/{running['id']}/cancel", {})[0] == 200
    assert fake_server.instances[0].interrupts == 1
    generator.release.set()
    job = client.wait(running["id"], "cancelled", "done")
    assert (job["state"], job["result"]) == ("cancelled", None)
    assert generator.jobs == [running["id"]]
    assert client.post(f"/api/jobs/{running['id']}/cancel", {})[0] == 409
    assert client.post("/api/jobs/nope/cancel", {})[0] == 404


def test_every_result_has_a_sidecar_with_the_provenance(
    make_studio, serve, fake_film, tmp_path
) -> None:
    client = serve(make_studio(real()))
    outpaint = client.wait(submit(client, OUTPAINT)["id"], "done")
    video = client.wait(submit(client, VIDEO)["id"], "done")
    texts = {}
    for job in (outpaint, video):
        status, text = client.get(f"/api/file?ref={job['sidecar']['ref']}")
        assert status == 200
        texts[job["kind"]] = text.decode()
        for line in (
            "- Source working copy: ",
            "IMG_0001.png`",
            "- GPU: cuda:0 Fake GPU",
            "- Render time: 1.5 s",
            "- Settings: ",
            "- Picked file: raw/IMG_0001.jpg\n",
            "- Studio GPU: index 1, NVIDIA RTX PRO 6000 Blackwell Max-Q Workstation Edition, "
            "GPU-11111111-1111-4111-8111-111111111111\n",
        ):
            assert line in texts[job["kind"]], (job["kind"], line)
    assert "- Extender: FLUX 3 Image Klein" in texts["outpaint"]
    assert "- Prompt: extend the room\n" in texts["outpaint"]
    assert "- Negative prompt: person\n" in texts["outpaint"]
    assert "- Seed: 42\n" in texts["outpaint"]
    assert (
        f"- Model: MiniMax H3 (FL2VA pruned bf16 transformer, 33B dense), short name minimax-h3, {H3_REVISION}"
        in texts["video"]
    )
    assert "`prompt=he smiles`" in texts["video"]
    assert "`negative_prompt=none: the graph has no negative conditioning input`" in texts["video"]
    assert "`seed=42`" in texts["video"]


def test_new_job_trashes_the_previous_result_of_the_same_source(
    make_studio, serve, trashed, tmp_path
) -> None:
    client = serve(make_studio())
    first = client.wait(submit(client, OUTPAINT)["id"], "done")
    other = client.wait(submit(client, VIDEO)["id"], "done")  # another kind stays
    second = client.wait(submit(client, {**OUTPAINT, "aspect": "4x3"})["id"], "done")
    jobs = tmp_path / "state/jobs"
    assert trashed == [jobs / first["id"]]
    listed = [job["id"] for job in client.get("/api/jobs")[1]["jobs"]]
    assert listed == [second["id"], other["id"]]


def test_server_stops_after_15_minutes_idle_and_on_close(make_studio, serve, fake_server) -> None:
    clock = [1000.0]
    studio = make_studio(clock=lambda: clock[0])
    client = serve(studio)
    client.wait(submit(client, OUTPAINT)["id"], "done")
    server = fake_server.instances[0]
    clock[0] += 899
    studio.tick()
    assert (server.stopped, studio.server) == (0, server)
    clock[0] += 1
    studio.tick()
    assert (server.stopped, studio.server) == (1, None)

    client.wait(submit(client, OUTPAINT)["id"], "done")
    studio.close()
    assert fake_server.instances[1].stopped == 1


def test_restart_lists_results_and_fails_interrupted_jobs(make_studio, serve, tmp_path) -> None:
    first = make_studio()
    client = serve(first)
    done = client.wait(submit(client, OUTPAINT)["id"], "done")
    first.close()
    jobs = tmp_path / "state/jobs"
    running = Job(
        id="20261027-120000-abcdef",
        kind="video",
        path=str(tmp_path / "tree/data/raw/IMG_0001.jpg"),
        label="raw/IMG_0001.jpg",
        gpu={"index": 1, "name": "GPU", "uuid": "GPU-x", "total_gb": 102.6},
        params=dict(VIDEO),
        created="2026-10-27T12:00:00+01:00",
        state="running",
        stage="sampling",
    )
    (jobs / running.id).mkdir()
    (jobs / running.id / "job.json").write_text(json.dumps(asdict(running)))

    client = serve(make_studio())
    listed = {job["id"]: job for job in client.get("/api/jobs")[1]["jobs"]}
    assert listed[done["id"]]["state"] == "done"
    assert client.get(f"/api/file?ref={listed[done['id']]['result']['ref']}")[0] == 200
    interrupted = listed[running.id]
    assert (interrupted["state"], interrupted["error"]) == ("failed", INTERRUPTED)
    assert json.loads((jobs / running.id / "job.json").read_text())["state"] == "failed"


PIPELINE = {**OUTPAINT, "video": {key: VIDEO[key] for key in ("prompt", "duration", "resolution")}}


def test_pipeline_runs_both_steps_on_the_gpu_chosen_for_the_clip(
    make_studio, serve, fake_server
) -> None:
    # GPU 1 holds the 21.317 GB frame but not the 68.823 GB clip: the pipeline needs GPU 2
    held_only = FAKE_SMI.replace("97887, 96000, 1100", "97887, 30000, 67887")
    client = serve(make_studio(gpus=fake_gpus(held_only)))
    frame = submit(client, PIPELINE)
    clip = next(job for job in client.get("/api/jobs")[1]["jobs"] if job["after"] == frame["id"])
    done_frame = client.wait(frame["id"], "done", "failed")
    done_clip = client.wait(clip["id"], "done", "failed")
    assert (done_frame["state"], done_clip["state"]) == ("done", "done"), (done_frame, done_clip)
    assert done_frame["gpu"]["uuid"] == GPU_2 == done_clip["gpu"]["uuid"]
    assert [server.launched.gpu for server in fake_server.instances] == [GPU_2]  # one server
    sidecar = client.get(f"/api/file?ref={done_clip['sidecar']['ref']}")[1].decode()
    assert "- Studio GPU: index 2" in sidecar


def test_pipeline_frees_the_frame_model_before_the_clip(make_studio, serve, fake_server) -> None:
    generator = FakeGenerator()
    client = serve(make_studio({"outpaint": generator, "video": generator}))
    frame = submit(client, PIPELINE)
    clip = next(job for job in client.get("/api/jobs")[1]["jobs"] if job["after"] == frame["id"])
    done_frame = client.wait(frame["id"], "done", "failed")
    done_clip = client.wait(clip["id"], "done", "failed")
    assert (done_frame["state"], done_clip["state"]) == ("done", "done"), (done_frame, done_clip)
    assert generator.jobs == [frame["id"], clip["id"]]  # the frame, then the clip
    assert generator.releases == [0, 1]  # freed after the frame, before the clip's prompt
    assert fake_server.instances[0].releases == 1  # one server, one model resident at a time
    assert done_clip["gpu"]["uuid"] == done_frame["gpu"]["uuid"]  # the clip keeps the frame's GPU


def test_pipeline_queues_the_video_of_the_frame_result_after_it(
    make_studio, serve, trashed, tmp_path
) -> None:
    frames = FakeGenerator(block=True)
    seen: list[tuple[str, list]] = []

    def video(job, server, folder):
        seen.append((job.path, list(trashed)))
        return FakeGenerator().run(job, server, folder)

    client = serve(make_studio({"outpaint": frames, "video": SimpleNamespace(run=video)}))
    frame = submit(client, PIPELINE)
    assert frames.started.wait(10)
    again = submit(client, OUTPAINT)  # the same source and kind, queued behind the video
    listed = client.get("/api/jobs")[1]["jobs"]
    assert [job["id"] for job in listed][::2] == [again["id"], frame["id"]]
    queued = listed[1]
    assert (queued["kind"], queued["after"], queued["state"]) == ("video", frame["id"], "queued")
    assert queued["params"]["prompt"] == VIDEO["prompt"] and frame["params"]["aspect"] == "16x9"
    frames.release.set()
    video_job = client.wait(queued["id"], "done")
    client.wait(again["id"], "done")
    result = tmp_path / "state/jobs" / frame["id"] / "IMG_0001.png"
    assert seen == [(str(result), [])]  # the frame was kept while its video waited and ran
    assert video_job["source"]["label"] == f"jobs/{frame['id']}/IMG_0001.png"
    assert frames.jobs == [frame["id"], again["id"]]
    assert trashed == [tmp_path / "state/jobs" / frame["id"]]  # the latest outpaint, afterwards


def test_pipeline_video_fails_with_the_frame_jobs_error(make_studio, serve) -> None:
    def fail(job, server, folder):
        raise RuntimeError("the frame step failed")

    video = FakeGenerator()
    client = serve(make_studio({"outpaint": SimpleNamespace(run=fail), "video": video}))
    frame = submit(client, PIPELINE)
    queued = client.get("/api/jobs")[1]["jobs"][0]
    assert client.wait(frame["id"], "failed")["error"] == "the frame step failed"
    failed = client.wait(queued["id"], "failed")
    assert (failed["error"], failed["result"], video.jobs) == ("the frame step failed", None, [])
    bad = {**PIPELINE, "video": {**PIPELINE["video"], "duration": 7}}
    assert client.post("/api/jobs", bad)[0] == 400
    assert client.post("/api/jobs", {**VIDEO, "video": PIPELINE["video"]})[0] == 400
    assert len(client.get("/api/jobs")[1]["jobs"]) == 2  # a refused pipeline queues nothing


def test_pipeline_video_fails_when_its_frame_is_cancelled_while_queued(make_studio, serve):
    blocker, video = FakeGenerator(block=True), FakeGenerator()
    client = serve(make_studio({"outpaint": blocker, "video": video}))
    submit(client, {**OUTPAINT, "ref": "1/IMG_0003.png"})  # runs, another source
    assert blocker.started.wait(10)
    frame = submit(client, PIPELINE)
    queued = next(job for job in client.get("/api/jobs")[1]["jobs"] if job["after"] == frame["id"])
    assert client.post(f"/api/jobs/{frame['id']}/cancel", {})[0] == 200
    blocker.release.set()
    failed = client.wait(queued["id"], "failed")
    assert (failed["error"], video.jobs) == (f"the frame job {frame['id']} was cancelled", [])


def test_pipeline_cancelled_frame_with_earlier_outpaint_of_the_same_source(make_studio, serve):
    """An earlier outpaint of the source starts, so the latest-result rule removes the cancelled
    frame job from the table before its video is taken; the worker fails the video and runs on."""
    blocker, video = FakeGenerator(block=True), FakeGenerator()
    client = serve(make_studio({"outpaint": blocker, "video": video}))
    other = {**OUTPAINT, "ref": "1/IMG_0003.png"}
    submit(client, other)  # runs, another source
    assert blocker.started.wait(10)
    earlier = submit(client, OUTPAINT)  # queued, the pipeline's source
    frame = submit(client, PIPELINE)
    queued = next(job for job in client.get("/api/jobs")[1]["jobs"] if job["after"] == frame["id"])
    assert client.post(f"/api/jobs/{frame['id']}/cancel", {})[0] == 200
    blocker.release.set()
    client.wait(earlier["id"], "done")
    failed = client.wait(queued["id"], "failed")
    assert (failed["error"], video.jobs) == (f"the frame job {frame['id']} was cancelled", [])
    assert frame["id"] not in [job["id"] for job in client.get("/api/jobs")[1]["jobs"]]
    later = submit(client, other)  # the worker still runs
    assert client.wait(later["id"], "done", "failed")["state"] == "done"
