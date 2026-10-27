"""Tests for the GPU-free helpers of henryk_media.animation.image_to_video."""

from contextlib import nullcontext
from dataclasses import replace
import json
import os
from pathlib import Path

import pytest

from henryk_media.animation import image_to_video as i2v
from henryk_media.animation.common import ClipResult, checkpoint_path, save_result
from henryk_media.animation.frame_interpolation import pairs, schedule

SETUP = i2v.Setup(
    model="Test model",
    revision="Test weights@abc",
    gpu="GPU-test",
    port=8190,
    native_fps=24.0,
    launch_command="true",
    stop_command="true",
    io_dirs={},
    graph=Path("/graph.json"),
)


def test_fill_replaces_markers_keeping_types_and_leaves_the_graph_unchanged() -> None:
    graph = {"1": {"image": "{{IMAGE}}", "width": "{{WIDTH}}", "n": [1, "{{SEED}}", "keep"]}}
    filled = i2v.fill(graph, {"{{IMAGE}}": "a.png", "{{WIDTH}}": 768, "{{SEED}}": 42})
    assert filled == {"1": {"image": "a.png", "width": 768, "n": [1, 42, "keep"]}}
    assert graph["1"]["image"] == "{{IMAGE}}"


def test_saved_video_returns_the_last_mp4_of_a_finished_graph() -> None:
    entry = {
        "outputs": {
            "26": {"images": [{"filename": "first.mp4", "subfolder": ""}]},
            "27": {"images": [{"filename": "clip_00001_.mp4", "subfolder": "a"}]},
        }
    }
    assert i2v.saved_video(entry)["filename"] == "clip_00001_.mp4"


def test_saved_video_rejects_a_graph_that_saved_no_mp4() -> None:
    with pytest.raises(RuntimeError):
        i2v.saved_video({"outputs": {"1": {"images": [{"filename": "frame.png"}]}}})


def test_setup_load_keeps_the_gpu_uuid_and_the_io_folders(tmp_path: Path) -> None:
    data = {
        "model": "Test model",
        "revision": "weights@abc",
        "gpu": "GPU-test (nvidia-smi index 1, Test GPU, 96 GB)",
        "port": 8190,
        "native_fps": 24,
        "launch_command": "start",
        "stop_command": "stop",
        "io_dirs": {"input": "/io/input", "output": "/io/output", "temp": "/io/temp/temp"},
        "workflow_api_path": "/tmp/graph.json",
    }
    path = tmp_path / "setup.json"
    path.write_text(json.dumps(data))
    setup = i2v.Setup.load(path)
    assert setup.gpu == "GPU-test"
    assert setup.native_fps == 24
    assert setup.io_dirs["temp"] == Path("/io/temp/temp")
    assert setup.graph == Path("/tmp/graph.json")

    del data["revision"]
    data["repository"] = "Test repo, revision abc"
    path.write_text(json.dumps(data))
    assert i2v.Setup.load(path).revision == "Test repo, revision abc"


def test_clip_settings_records_markers_model_settings_interpolation_and_source(
    tmp_path: Path,
) -> None:
    source = tmp_path / "IMG_1.png"
    source.write_bytes(b"photo")
    settings = i2v.clip_settings(
        SETUP,
        {"{{PROMPT}}": "make it live", "{{NEGATIVE_PROMPT}}": "blurry", "{{SEED}}": 42},
        {"steps": 30, "cfg": 3.0},
        source,
    )
    assert settings == {
        "prompt": "make it live",
        "negative_prompt": "blurry",
        "seed": 42,
        "steps": 30,
        "cfg": 3.0,
        "native_fps": 24.0,
        "fps": 30,
        "frames": 300,
        "interpolation": i2v.INTERPOLATION,
        "source_mtime_ns": source.stat().st_mtime_ns,
        "source_bytes": 5,
    }


def test_schedule_delivers_150_frames_at_30_fps_and_keeps_30_native_frames() -> None:
    steps = schedule(121, 24.0, 30.0, 150)
    assert len(steps) == 150
    assert steps[0] == (0, 0.0)
    assert all(0 <= index < 121 and 0.0 <= fraction < 1.0 for index, fraction in steps)
    assert sum(fraction == 0.0 for _, fraction in steps) == 30  # every fifth frame is native
    moments = [(index + fraction) / 24.0 for index, fraction in steps]
    assert moments == sorted(moments)
    assert moments[-1] == pytest.approx(149 / 30)


def test_schedule_places_each_output_frame_at_its_exact_time() -> None:
    steps = schedule(81, 16.0, 30.0, 150)
    assert len(steps) == 150
    for frame, (index, fraction) in enumerate(steps):
        assert (index + fraction) / 16.0 == pytest.approx(frame / 30.0)
    assert sum(fraction == 0.0 for _, fraction in steps) == 10  # every fifteenth frame is native


def test_schedule_rejects_a_clip_too_short_for_the_requested_frames() -> None:
    with pytest.raises(ValueError):
        schedule(121, 24.0, 30.0, 152)  # frame 151 lies past the last native frame


def test_schedule_rejects_a_clip_with_one_frame() -> None:
    with pytest.raises(ValueError):
        schedule(1, 24.0, 30.0, 150)


def test_pairs_groups_only_the_synthesized_frames_by_native_pair() -> None:
    grouped = pairs(schedule(121, 24.0, 30.0, 150))
    assert grouped[0] == [(1, 0.8)]
    assert set(grouped) == set(range(120))  # every native pair holds one synthesized frame
    assert sum(len(group) for group in grouped.values()) == 120  # 150 frames minus 30 native


def test_interpolate_runs_the_worker_in_the_comfyui_environment(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    calls: dict = {}
    monkeypatch.setattr(i2v.subprocess, "run", lambda command, **kwargs: calls.update(
        command=command, kwargs=kwargs
    ))
    i2v.interpolate(tmp_path / "native.mp4", tmp_path / "clip.mp4", "GPU-test")
    assert calls["command"][0] == str(i2v.COMFYUI_PYTHON)
    assert calls["command"][1] == str(i2v.FRAME_INTERPOLATION_SCRIPT)
    assert calls["command"][-4:] == ["--fps", "30", "--frames", "300"]
    assert calls["kwargs"]["cwd"] == i2v.COMFYUI_DIR
    assert calls["kwargs"]["env"]["CUDA_VISIBLE_DEVICES"] == "GPU-test"
    assert calls["kwargs"]["env"]["PYTHONPATH"] == str(i2v.COMFYUI_DIR)


def test_free_gpu_unloads_the_server_models_only_when_film_does_not_fit(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    server = object.__new__(i2v.Server)
    server.setup = SETUP
    calls = []
    monkeypatch.setattr(i2v, "api", lambda *args: calls.append(args))
    monkeypatch.setattr(i2v.time, "sleep", lambda seconds: None)

    monkeypatch.setattr(i2v, "gpu_free_mib", lambda gpu: i2v.INTERPOLATION_MIB)
    server.free_gpu()
    assert calls == []

    room = iter([i2v.INTERPOLATION_MIB - 1, i2v.INTERPOLATION_MIB])
    monkeypatch.setattr(i2v, "gpu_free_mib", lambda gpu: next(room))
    server.free_gpu()
    assert calls == [(SETUP.port, "/free", {"unload_models": True, "free_memory": True})]


def test_render_restores_only_a_clip_that_probes_as_300_frames_at_30_fps(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    graph = tmp_path / "graph.json"
    graph.write_text(json.dumps({"1": {"image": "{{IMAGE}}", "prefix": "{{FILENAME_PREFIX}}"}}))
    source = tmp_path / "IMG_1.png"
    source.write_bytes(b"photo")
    clip = tmp_path / "IMG_1.mp4"
    values = {"{{PROMPT}}": "make it live", "{{SEED}}": 42}
    settings = {"steps": 30}
    setup = replace(
        SETUP, graph=graph, io_dirs={"input": tmp_path, "output": tmp_path, "temp": tmp_path}
    )
    finished = ClipResult(
        clip=str(clip),
        source="s",
        driving="",
        model=SETUP.model,
        revision=SETUP.revision,
        variant="prompt",
        settings=i2v.clip_settings(SETUP, values, settings, source),
        gpu="Test GPU",
        seconds=1.0,
        peak_vram_gb=0.0,
        width=16,
        height=16,
        frames=300,
        fps=30.0,
    )
    save_result(finished, clip)
    server = object.__new__(i2v.Server)
    server.setup = setup

    class Rendered(RuntimeError):
        pass

    def render_again(*args: object) -> None:
        raise Rendered("the clip was rendered again")

    monkeypatch.setattr(i2v.Server, "run", render_again)
    monkeypatch.setattr(i2v.Server, "photo_copy", lambda *args: nullcontext())

    # no clip: load_result finds no finished result
    with pytest.raises(Rendered, match="rendered again"):
        server.render(source, clip, "prompt", values, settings)

    # empty clip: the probe cannot read it
    clip.write_bytes(b"")
    with pytest.raises(Rendered, match="rendered again"):
        server.render(source, clip, "prompt", values, settings)

    # a probe that reports a wrong frame count or rate, or raises
    monkeypatch.setattr(i2v, "probe_clip", lambda path: (16, 16, 299, 30.0))
    with pytest.raises(Rendered, match="rendered again"):
        server.render(source, clip, "prompt", values, settings)
    monkeypatch.setattr(i2v, "probe_clip", lambda path: (16, 16, 300, 25.0))
    with pytest.raises(Rendered, match="rendered again"):
        server.render(source, clip, "prompt", values, settings)

    def probe_raises(path: Path) -> tuple[int, int, int, float]:
        raise RuntimeError("decoder failed")

    monkeypatch.setattr(i2v, "probe_clip", probe_raises)
    with pytest.raises(Rendered, match="rendered again"):
        server.render(source, clip, "prompt", values, settings)

    # 300 frames at 30 fps restore the checkpoint without rendering
    monkeypatch.setattr(i2v, "probe_clip", lambda path: (16, 16, 300, 30.0))
    assert server.render(source, clip, "prompt", values, settings) == finished

    # a truncated checkpoint is ignored: the clip is rendered again instead of raising
    checkpoint = checkpoint_path(clip)
    checkpoint.write_text(checkpoint.read_text()[:20])
    with pytest.raises(Rendered, match="rendered again"):
        server.render(source, clip, "prompt", values, settings)

    # valid JSON of the wrong shape is ignored too
    checkpoint.write_text("[]")
    with pytest.raises(Rendered, match="rendered again"):
        server.render(source, clip, "prompt", values, settings)

    # a checkpoint that is not UTF-8 text (a binary or UTF-16 file) is ignored as well
    checkpoint.write_bytes(b"\xff\xfe\x00")
    with pytest.raises(Rendered, match="rendered again"):
        server.render(source, clip, "prompt", values, settings)


def test_restore_matches_notices_a_source_rewritten_in_place(tmp_path: Path) -> None:
    source = tmp_path / "IMG_1.png"
    source.write_bytes(b"photo")
    values = {"{{PROMPT}}": "make it live"}
    settings = {"steps": 30}
    finished = ClipResult(
        clip="clip.mp4",
        source="s",
        driving="",
        model=SETUP.model,
        revision=SETUP.revision,
        variant="prompt",
        settings=i2v.clip_settings(SETUP, values, settings, source),
        gpu="Test GPU",
        seconds=1.0,
        peak_vram_gb=0.0,
        width=16,
        height=16,
        frames=300,
        fps=30.0,
    )
    assert i2v.restore_matches(finished, SETUP, i2v.clip_settings(SETUP, values, settings, source))
    mtime = source.stat().st_mtime_ns
    source.write_bytes(b"other")  # five bytes, as before: only the mtime changes
    os.utime(source, ns=(source.stat().st_atime_ns, mtime + 1_000_000_000))
    assert not i2v.restore_matches(
        finished, SETUP, i2v.clip_settings(SETUP, values, settings, source)
    )


def test_render_rejects_wrong_interpolated_frames_or_rate(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    graph = tmp_path / "graph.json"
    graph.write_text(json.dumps({"1": {"image": "{{IMAGE}}", "prefix": "{{FILENAME_PREFIX}}"}}))
    source = tmp_path / "IMG_1.png"
    source.write_bytes(b"photo")
    clip = tmp_path / "IMG_1.mp4"
    setup = replace(
        SETUP,
        graph=graph,
        io_dirs={"input": tmp_path, "output": tmp_path, "temp": tmp_path},
    )
    server = object.__new__(i2v.Server)
    server.setup = setup
    server.baseline_mib = 0
    server.stats = {"devices": [{"name": "Test GPU"}]}
    monkeypatch.setattr(
        i2v.Server,
        "run",
        lambda *args: (
            {"outputs": {"1": {"images": [{"filename": "clip.mp4", "subfolder": ""}]}}},
            1.0,
            0,
        ),
    )
    monkeypatch.setattr(i2v.Server, "photo_copy", lambda *args: nullcontext())
    monkeypatch.setattr(i2v.Server, "free_gpu", lambda *args: None)
    monkeypatch.setattr(i2v, "interpolate", lambda *args: None)
    monkeypatch.setattr(i2v, "trash", lambda *args: None)
    monkeypatch.setattr(i2v.shutil, "move", lambda *args: None)
    monkeypatch.setattr(i2v, "project_relative", str)
    native = setup.io_dirs["temp"] / f"{clip.stem}-native.mp4"
    measured = {"frames": 299, "fps": 30.0}

    def fake_probe(path: Path) -> tuple[int, int, int, float]:
        if path == native:
            return 16, 16, 242, 24.0
        return 16, 16, measured["frames"], measured["fps"]

    monkeypatch.setattr(i2v, "probe_clip", fake_probe)
    values = {"{{PROMPT}}": "make it live"}
    settings = {"steps": 30}

    for frames, fps in ((299, 30.0), (300, 25.0)):
        measured.update(frames=frames, fps=fps)
        with pytest.raises(
            RuntimeError,
            match=f"{frames} frames at {fps:g} fps, expected 300 frames at 30 fps",
        ):
            server.render(source, clip, "prompt", values, settings)
    measured.update(frames=300, fps=30.0)
    result = server.render(source, clip, "prompt", values, settings)
    assert (result.frames, result.fps) == (300, 30.0)
