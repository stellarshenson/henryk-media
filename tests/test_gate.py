"""Tests for the no-new-people gate's pure rules: panels, inside fraction and verdict text."""

from henryk_media.imaging.gate import (
    detection_kind,
    detection_text,
    inside_fraction,
    panels,
    touches_border,
)
from henryk_media.imaging.provenance import gate_lines

FRAME = 1704  # synthetic frame width; the panel rules do not depend on the bench geometry
LEFT = 371  # synthetic pad on each side of the 962 px photo
PHOTO = 962
RANGES = panels(FRAME, LEFT, PHOTO)


def test_panels_are_the_two_side_strips() -> None:
    assert RANGES == ((0, LEFT), (LEFT + PHOTO, FRAME))


def test_box_wholly_inside_a_panel_is_fully_inside() -> None:
    assert inside_fraction((100.0, 0.0, 300.0, 500.0), RANGES) == 1.0


def test_box_straddling_the_seam_counts_half_inside() -> None:
    assert inside_fraction((321.0, 0.0, 421.0, 100.0), RANGES) == 0.5


def test_face_rule_rejects_only_a_box_wholly_inside_a_panel() -> None:
    assert detection_kind("face", 1.0) == "stranger"
    assert detection_kind("face", 0.999) == "continuation"


def test_face_rule_calls_a_box_crossing_the_photo_a_continuation() -> None:
    assert detection_kind("face", 0.5) == "continuation"
    assert detection_kind("face", 0.0) is None


def test_person_rule_rejects_only_a_box_wholly_inside_a_panel() -> None:
    assert detection_kind("person", 1.0) == "stranger"
    assert detection_kind("person", 0.999) is None


def test_person_rule_keeps_a_box_that_touches_the_photo() -> None:
    assert inside_fraction((271.0, 0.0, 471.0, 100.0), RANGES) == 0.5
    assert detection_kind("person", inside_fraction((271.0, 0.0, 471.0, 100.0), RANGES)) is None


def test_person_rule_calls_a_box_on_the_frame_border_clipped() -> None:
    box = (0.0, 249.0, 13.0, 373.0)  # the 16:9 sliver the Star Colonel judged not a person
    assert touches_border(box, (1280, 720))
    assert detection_kind("person", 1.0, touches_border(box, (1280, 720))) == "clipped"


def test_border_tolerance_is_two_pixels_on_every_side() -> None:
    size = (1280, 960)
    assert touches_border((2.0, 100.0, 300.0, 400.0), size)  # left, at the tolerance
    assert not touches_border((2.1, 100.0, 300.0, 400.0), size)  # clear of it
    assert touches_border((100.0, 2.0, 300.0, 400.0), size)  # top
    assert touches_border((100.0, 100.0, 1278.0, 400.0), size)  # right
    assert touches_border((100.0, 100.0, 300.0, 958.0), size)  # bottom


def test_detection_text_names_the_box_and_its_panel_fraction() -> None:
    item = {
        "detector": "face",
        "confidence": 0.7412,
        "box": [12.4, 30.6, 120.2, 200.0],
        "inside": 1.0,
    }
    assert detection_text(item) == "face 0.74 box (12,31,120,200) inside 1.00"


def test_gate_lines_state_a_pass_with_counts_and_kept_seed() -> None:
    gate = {
        "passed": True,
        "seed": 42,
        "panels": [[0, LEFT], [LEFT + PHOTO, FRAME]],
        "rule": "face or person box wholly inside an added panel",
        "detectors": {"face": "face_yolov8n.pt", "person": "yolo11n.pt"},
        "rejected": [],
    }
    text = gate_lines(gate)
    assert "- Gate: passed; kept seed 42; strangers 0; continuations 0" in text
    assert "- Gate strangers: none" in text
    assert "- Gate continuations: none" in text


def test_gate_lines_list_the_kept_tiles_strangers_and_continuations() -> None:
    gate = {
        "passed": False,
        "seed": 47,
        "panels": [[0, LEFT], [LEFT + PHOTO, FRAME]],
        "rule": "face or person box wholly inside an added panel",
        "detectors": {"face": "face_yolov8n.pt"},
        "rejected": [
            {
                "seed": 46,
                "scale": 1.0,
                "violations": [
                    {
                        "detector": "person",
                        "confidence": 0.55,
                        "box": [1400.0, 10.0, 1600.0, 900.0],
                        "inside": 1.0,
                    }
                ],
            },
            {
                "seed": 47,
                "scale": 1.0,
                "violations": [
                    {
                        "detector": "person",
                        "confidence": 0.28,
                        "box": [0.0, 249.0, 13.0, 373.0],
                        "inside": 1.0,
                    }
                ],
            },
        ],
        "continuations": [
            {
                "detector": "face",
                "confidence": 0.85,
                "box": [312.1, 60.7, 391.4, 162.3],
                "inside": 0.717429,
            }
        ],
    }
    text = gate_lines(gate)
    assert "- Gate: FAILED; kept seed 47; strangers 1; continuations 1" in text
    assert "person 0.28 box (0,249,13,373) inside 1.00" in text
    assert "face 0.85 box (312,61,391,162) inside 0.72" in text
    assert "seed 46" not in text  # only the kept tile's strangers are listed


def test_gate_lines_state_the_clipped_count_beside_the_other_counts() -> None:
    gate = {
        "passed": True,
        "seed": 47,
        "panels": [[0, LEFT], [LEFT + PHOTO, FRAME]],
        "rule": "clipped: a box touching the frame's outer border",
        "detectors": {"person": "yolo11n.pt"},
        "rejected": [],
        "clipped": [
            {
                "detector": "person",
                "confidence": 0.284,
                "box": [0.0, 249.0, 13.0, 373.0],
                "inside": 1.0,
            }
        ],
    }
    text = gate_lines(gate)
    assert "- Gate: passed; kept seed 47; strangers 0; continuations 0; clipped 1" in text
    assert "person 0.28 box (0,249,13,373) inside 1.00" in text


def test_gate_lines_say_so_when_no_gate_was_recorded() -> None:
    assert gate_lines({}) == "- Gate: not recorded\n"
