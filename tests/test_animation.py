"""Tests for the GPU-free helpers of henryk_media.animation."""

from dataclasses import replace
import itertools
from pathlib import Path
from statistics import median

import pytest

from henryk_media.animation.advanced_liveportrait import (
    FPS,
    FRAMES,
    KEYFRAME_STEP,
    Motion,
    build_graph,
    command,
    expression_at,
    head_steps,
    keyframes,
    logged_faces,
    restore,
    settings,
)
from henryk_media.animation.common import (
    ClipResult,
    checkpoint_path,
    clip_path,
    load_result,
    output_dir,
    save_result,
    sidecar_text,
)
from henryk_media.config import PROCESSED_DATA_DIR


@pytest.fixture
def result() -> ClipResult:
    """A clip result as LivePortrait's wrapper would return it."""
    return ClipResult(
        clip="data/processed/set/liveportrait/IMG_1--exp.mp4",
        source="data/interim/set/IMG_1.png",
        driving="data/external/driving-clips/idle-3s.mp4",
        model="LivePortrait",
        revision="code KwaiVGI/LivePortrait@abc, weights KlingTeam/LivePortrait@def",
        variant="exp",
        settings={"flag_pasteback": True, "animation_region": "exp"},
        gpu="Test GPU",
        seconds=12.345,
        peak_vram_gb=1.5,
        width=962,
        height=1278,
        frames=90,
        fps=30.0,
    )


def test_output_dir_is_model_folder_under_processed_photo_set() -> None:
    assert output_dir("set", "liveportrait") == PROCESSED_DATA_DIR / "set" / "liveportrait"


def test_clip_path_names_stem_and_variant() -> None:
    clip = clip_path(Path("/out"), Path("/any/dir/IMG_1.png"), "all")
    assert clip == Path("/out/IMG_1--all.mp4")


def test_checkpoint_path_sits_in_checkpoints_beside_clip() -> None:
    assert checkpoint_path(Path("/out/IMG_1--all.mp4")) == Path("/out/checkpoints/IMG_1--all.json")


def test_sidecar_text_carries_provenance_and_measurements(result: ClipResult) -> None:
    text = sidecar_text(result)
    assert text.startswith("# IMG_1--exp.mp4\n")
    assert "- Source working copy: `data/interim/set/IMG_1.png`" in text
    assert "weights KlingTeam/LivePortrait@def" in text
    assert "`flag_pasteback=True`, `animation_region=exp`" in text
    assert "962 x 1278 px, 90 frames at 30 fps (3.00 s)" in text
    assert "- Render time: 12.3 s" in text
    assert "- Peak VRAM: 1.50 GB" in text


def test_load_result_needs_clip_and_checkpoint(result: ClipResult, tmp_path: Path) -> None:
    clip = tmp_path / "IMG_1--exp.mp4"
    assert load_result(clip) is None
    save_result(result, clip)
    assert load_result(clip) is None  # checkpoint without the video is not a finished clip
    clip.write_bytes(b"")
    assert load_result(clip) == result
    assert clip.with_suffix(".md").read_text() == sidecar_text(result)


SOFT = Motion(smile=0.28, yaw=3.5, pitch=1.2, roll=0.6, blink=-16.0)
STILL = Motion(smile=0.0, yaw=1.2, pitch=0.35, roll=0.2, blink=0.0)


def test_keyframes_start_at_the_photo_end_at_the_last_frame_and_lie_at_most_3_apart() -> None:
    frames_values = keyframes(SOFT)
    frames = [frame for frame, _ in frames_values]
    assert frames_values[0] == (0, dict.fromkeys(frames_values[0][1], 0.0))
    assert frames[-1] == FRAMES - 1
    assert all(b - a <= 3 for a, b in itertools.pairwise(frames))
    assert FRAMES == 150 and FPS == 30  # 5 s at 30 fps


def test_one_blink_closes_to_its_value_for_two_frames_within_0_4_s() -> None:
    blink = [expression_at(frame, SOFT)["blink"] for frame in range(FRAMES)]
    moving = [frame for frame, value in enumerate(blink) if value]
    assert moving == list(range(moving[0], moving[-1] + 1))  # one contiguous blink
    assert (moving[-1] - moving[0] + 2) / FPS <= 0.4  # open frame to open frame
    assert blink.count(SOFT.blink) == 2


def test_still_motion_has_no_blink_and_no_smile() -> None:
    frames_values = keyframes(STILL)
    assert all(values["blink"] == 0 and values["smile"] == 0 for _, values in frames_values)
    assert [frame for frame, _ in frames_values] == [*range(0, FRAMES, KEYFRAME_STEP), FRAMES - 1]


@pytest.mark.parametrize("motion", [SOFT, STILL])
def test_head_never_holds(motion: Motion) -> None:
    steps = head_steps(motion)
    assert len(steps) == FRAMES - 1
    assert min(steps[3:]) > 0.25 * median(steps)  # slowest only while starting


def test_yaw_turns_every_1_to_1_5_s_within_its_peak() -> None:
    yaw = [expression_at(frame, SOFT)["rotate_yaw"] for frame in range(FRAMES)]
    turns = [
        frame
        for frame, (before, here, after) in enumerate(zip(yaw, yaw[1:], yaw[2:]), start=1)
        if (here - before) * (after - here) < 0
    ]
    assert yaw[0] == 0 and max(map(abs, yaw)) == SOFT.yaw
    assert len(turns) == 3 and all(FPS <= b - a <= 1.5 * FPS for a, b in itertools.pairwise([0, *turns]))


def test_pitch_moves_up_and_down_but_never_lifts_the_chin_above_the_photo() -> None:
    pitch = [expression_at(frame, SOFT)["rotate_pitch"] for frame in range(FRAMES)]
    assert min(pitch) == 0 and max(pitch) == SOFT.pitch
    assert pitch != sorted(pitch)


def test_smile_builds_then_keeps_varying_between_60_and_100_percent() -> None:
    smile = [expression_at(frame, SOFT)["smile"] for frame in range(FRAMES)]
    peak = smile.index(SOFT.smile)
    assert smile[0] == 0 and smile[:peak] == sorted(smile[:peak])
    assert min(smile[peak:]) == pytest.approx(0.6 * SOFT.smile)
    assert all(after != before for before, after in itertools.pairwise(smile))


def test_command_reaches_keyframe_k_at_its_frame() -> None:
    assert command([0, 10, 14]) == "0=1:0\n1=10:0\n2=4:0"


@pytest.mark.parametrize("frames", [[1, 10], [0, 10, 10], [0, 12, 8]])
def test_command_rejects_frames_not_starting_at_0_or_not_increasing(frames: list[int]) -> None:
    with pytest.raises(ValueError):
        command(frames)


def test_build_graph_chains_one_editor_per_keyframe_into_a_30_fps_video() -> None:
    frames_values = keyframes(SOFT)
    graph = build_graph("photo.png", frames_values, "prefix")
    editors = [node for node in graph.values() if node["class_type"] == "ExpressionEditor"]
    animate = next(node for node in graph.values() if node["class_type"] == "AdvancedLivePortrait")
    video = next(node for node in graph.values() if node["class_type"] == "VHS_VideoCombine")
    assert graph["1"]["inputs"]["image"] == "photo.png"
    assert len(editors) == len(frames_values) - 1
    assert editors[0]["inputs"]["src_image"] == ["1", 0]
    assert editors[1]["inputs"]["motion_link"] == ["2", 1]
    assert animate["inputs"]["motion_link"] == [str(len(editors) + 1), 1]
    for editor, (_, values) in zip(editors, frames_values[1:], strict=True):
        assert values.items() <= editor["inputs"].items()
        assert editor["inputs"]["eyebrow"] == editor["inputs"]["aaa"] == 0
    steps = animate["inputs"]["command"].split("\n")
    assert sum(int(step.split("=")[1].split(":")[0]) for step in steps) == FRAMES
    assert video["inputs"]["frame_rate"] == FPS
    assert video["inputs"]["filename_prefix"] == "prefix"


def test_build_graph_needs_a_keyframe_after_frame_0() -> None:
    with pytest.raises(ValueError):
        build_graph("photo.png", keyframes(SOFT)[:1], "prefix")


def test_restore_returns_a_clip_only_for_the_same_motion(result: ClipResult, tmp_path: Path) -> None:
    clip = tmp_path / "IMG_1--soft.mp4"
    clip.write_bytes(b"")
    save_result(replace(result, settings=settings(SOFT)), clip)
    assert restore(clip, SOFT).settings == settings(SOFT)
    assert restore(clip, replace(SOFT, smile=0.1)) is None
    save_result(replace(result, settings={**settings(SOFT), "smile_knots": "10:0 60:1"}), clip)
    assert restore(clip, SOFT) is None  # same peak values, other curve


NODE_LOG = """\
0: 640x512 3 faces, 9.0ms
Speed: 2.1ms preprocess, 9.0ms inference, 1.2ms postprocess per image at shape (1, 3, 640, 512)
w, h:(962, 1278)
diff, min_diff, best_box:(np.float32(395.5), 962, [np.float32(793.2), np.float32(290.7), np.float32(959.8), np.float32(527.9)])
diff, min_diff, best_box:(np.float32(36.2), np.float32(268.7), [np.float32(409.6), np.float32(275.8), np.float32(624.8), np.float32(546.0)])
"""


def test_logged_faces_reads_the_face_count_and_the_printed_boxes_last_is_animated() -> None:
    count, boxes = logged_faces(NODE_LOG)
    assert count == 3
    assert boxes == [(793, 291, 960, 528), (410, 276, 625, 546)]


def test_logged_faces_rejects_a_log_without_detection() -> None:
    with pytest.raises(ValueError):
        logged_faces("Prompt executed in 0.1 seconds\n")
