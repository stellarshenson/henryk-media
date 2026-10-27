"""Tests for the image extender's pure helpers: geometry, tone match, paste-back and provenance."""

import json
from pathlib import Path
import re

import numpy as np
from PIL import Image

from henryk_media.imaging.composite import (
    Geometry,
    crop,
    feather_mask,
    interior_matches,
    paste,
    render_size,
    seam_metrics,
    target_size,
    tone_match,
)
from henryk_media.imaging.gate import detection_kind, inside_fraction, panels, touches_border
from henryk_media.imaging import registry
from henryk_media.imaging.grids import Tile, contact_sheet
from henryk_media.imaging.provenance import (
    ExtendResult,
    UpscaleResult,
    load_extend,
    load_upscale,
    save_extend,
    save_upscale,
)
from henryk_media.imaging.setup import Setup

PHOTO = (962, 1278)  # width, height of the birthday photo


def noisy_photo(width: int, height: int) -> Image.Image:
    """Return a deterministic RGB image, so every pixel differs from a flat fill."""
    rng = np.random.default_rng(0)
    return Image.fromarray(rng.integers(0, 256, (height, width, 3), dtype=np.uint8), mode="RGB")


def extent() -> ExtendResult:
    """Return a filled extension record for a 4:3 frame."""
    return ExtendResult(
        image="data/processed/x/4x3/qwen/IMG_8564.png",
        source="data/interim/x/IMG_8564.png",
        extender="qwen-inpainting",
        aspect="4x3",
        prompt="continue the room",
        negative_prompt="",
        seed=42,
        model="Qwen-Image",
        weights="Comfy-Org/Qwen-Image",
        licence="Apache-2.0",
        settings={"steps": 20, "frame": {"pad_left": 278}},
        geometry={
            "pad_left": 278,
            "pad_right": 279,
            "pad_top": 0,
            "pad_bottom": 0,
            "feather": 8,
            "width": 1280,
            "height": 960,
        },
        gpu="RTX PRO 6000 Blackwell",
        seconds=40.5,
        peak_vram_gb=30.5,
        render_width=1280,
        render_height=960,
        photo_width=962,
        photo_height=1278,
        width=1280,
        height=960,
        ratio=1.3333,
        tone_matched=True,
    )


def test_frame_geometry_is_exact_at_both_aspects() -> None:
    four_three = Geometry.for_aspect(PHOTO, 4 / 3)
    assert (four_three.width, four_three.height) == (1280, 960)
    assert four_three.photo_size(PHOTO) == (723, 960)  # scaled to the frame height
    assert four_three.resized(Image.new("RGB", PHOTO)).size == (723, 960)
    assert (four_three.pad_left, four_three.pad_right) == (278, 279)  # the odd column on the right
    assert four_three.extended(PHOTO) == (1280, 960)
    assert four_three.origin(PHOTO) == (278, 0)
    assert four_three.width / four_three.height == 4 / 3
    sixteen_nine = Geometry.for_aspect(PHOTO, 16 / 9)
    assert (sixteen_nine.width, sixteen_nine.height) == (1280, 720)
    assert sixteen_nine.photo_size(PHOTO) == (542, 720)
    assert (sixteen_nine.pad_left, sixteen_nine.pad_right) == (369, 369)
    assert sixteen_nine.extended(PHOTO) == (1280, 720)
    assert sixteen_nine.width / sixteen_nine.height == 16 / 9


def test_frame_width_leads_and_the_photo_scales_to_the_height() -> None:
    """A square or tall photo changes the side pads, never the frame's 1280 px width."""
    square = Geometry.for_aspect((1000, 1000), 4 / 3)
    assert (square.width, square.height) == (1280, 960)
    assert square.photo_size((1000, 1000)) == (960, 960)
    assert (square.pad_left, square.pad_right) == (160, 160)
    tall = Geometry.for_aspect((600, 1200), 16 / 9)
    assert (tall.width, tall.height) == (1280, 720)
    assert tall.photo_size((600, 1200)) == (360, 720)
    assert (tall.pad_left, tall.pad_right) == (460, 460)


FOUR_THREE_PANELS = panels(1280, 278, 723)  # 4:3 bench frame: photo at x 278 to 1001


def test_gate_calls_a_face_wholly_inside_a_panel_a_stranger() -> None:
    inside = inside_fraction((100.0, 120.0, 200.0, 300.0), FOUR_THREE_PANELS)
    assert inside == 1.0
    assert detection_kind("face", inside) == "stranger"


def test_gate_calls_a_face_crossing_the_photo_edge_a_continuation() -> None:
    inside = inside_fraction((150.0, 100.0, 330.0, 300.0), FOUR_THREE_PANELS)
    assert 0.0 < inside < 1.0
    assert detection_kind("face", inside) == "continuation"


def test_gate_calls_a_person_wholly_inside_a_panel_and_clear_of_the_border_a_stranger() -> None:
    box = (1050.0, 100.0, 1200.0, 500.0)
    inside = inside_fraction(box, FOUR_THREE_PANELS)
    assert inside == 1.0
    assert not touches_border(box, (1280, 960))
    assert detection_kind("person", inside, touches_border(box, (1280, 960))) == "stranger"


def test_gate_calls_a_person_box_on_the_frame_border_clipped() -> None:
    """The flux3-klein boxes that failed the judged-good tiles: easel leg, cloth and floor."""
    four_three = (0.0, 1.0, 106.0, 439.0)
    assert inside_fraction(four_three, FOUR_THREE_PANELS) == 1.0
    assert touches_border(four_three, (1280, 960))
    assert detection_kind("person", 1.0, touches_border(four_three, (1280, 960))) == "clipped"
    sixteen_nine_panels = panels(1280, 369, 542)  # 16:9 bench frame: photo at x 369 to 911
    sliver = (0.0, 249.0, 13.0, 373.0)
    assert inside_fraction(sliver, sixteen_nine_panels) == 1.0
    assert touches_border(sliver, (1280, 720))
    assert detection_kind("person", 1.0, touches_border(sliver, (1280, 720))) == "clipped"


def test_upscale_sizes_double_each_side_and_respect_the_stride() -> None:
    assert target_size((1280, 960)) == (2560, 1920)
    assert target_size((1280, 720)) == (2560, 1440)
    assert render_size((2560, 1923)) == (2560, 1928)
    frame = Image.new("RGB", (2560, 1928))
    assert crop(frame, (2560, 1923)).size == (2560, 1923)


def test_feather_mask_is_opaque_from_the_feather_band_inward() -> None:
    mask = np.asarray(feather_mask((20, 30), 8))
    assert mask[0, 0] == round(1 / 8 * 255)  # outermost border pixel, mostly fill
    assert mask[3, 10] == round(4 / 8 * 255)  # halfway up the ramp
    assert mask[7, 10] == 255  # eight pixels in, fully opaque
    assert mask[15, 10] == 255  # centre


def test_paste_keeps_the_interior_and_blends_the_border() -> None:
    fill = Image.new("RGB", (100, 80), (30, 60, 90))
    photo = noisy_photo(40, 30)
    pasted = paste(fill, photo, (20, 10), 4)
    assert interior_matches(pasted, photo, (20, 10), 4)
    assert np.array_equal(
        np.asarray(pasted.crop((0, 0, 20, 80))), np.asarray(fill.crop((0, 0, 20, 80)))
    )
    outside = np.asarray(pasted.crop((60, 0, 100, 80)))
    assert np.array_equal(outside, np.asarray(fill.crop((60, 0, 100, 80))))
    border = np.asarray(pasted.crop((20, 10, 60, 11))).astype(int)
    photo_row = np.asarray(photo.crop((0, 0, 40, 1))).astype(int)
    assert np.abs(border - photo_row).max() > 0  # the border blends, not a hard paste


def test_interior_matches_detects_a_changed_pixel() -> None:
    photo = noisy_photo(40, 30)
    altered = photo.copy()
    altered.putpixel((20, 15), (255, 0, 0))
    assert not interior_matches(altered, photo, (0, 0), 4)


def test_tone_match_equalises_mean_and_std_over_the_photo_region() -> None:
    photo = noisy_photo(40, 30)
    frame = Image.new("RGB", (80, 50), (120, 120, 120))
    frame.paste(photo.point(lambda value: value // 2 + 40), (20, 10))
    matched = tone_match(frame, photo, (20, 10))
    region = np.asarray(matched.crop((20, 10, 60, 40)), dtype=float)
    target = np.asarray(photo, dtype=float)
    for channel in range(3):
        assert abs(region[..., channel].mean() - target[..., channel].mean()) < 0.6
        assert abs(region[..., channel].std() - target[..., channel].std()) < 0.6


def test_seam_metrics_report_a_smooth_continuation() -> None:
    columns = np.arange(80, dtype=np.uint8) * 3
    frame = Image.fromarray(np.tile(columns, (30, 1))[:, :, None].repeat(3, axis=2), mode="RGB")
    metrics = seam_metrics(frame, (20, 0), (40, 30))
    assert metrics["left_seam"] < 1.5  # a linear gradient continues at its own slope
    assert metrics["right_seam"] < 1.5
    assert metrics["panel_std"] > 0  # the panels are not flat


def test_seam_metrics_flag_a_visible_seam() -> None:
    frame = Image.new("RGB", (80, 30), (0, 0, 0))
    inner = Image.new("RGB", (40, 30), (255, 255, 255))
    frame.paste(inner, (20, 0))
    metrics = seam_metrics(frame, (20, 0), (40, 30))
    assert metrics["left_seam"] > 100  # black to white across the border


def test_extend_result_round_trip(tmp_path: Path) -> None:
    image = tmp_path / "IMG_0001.png"
    Image.new("RGB", (1280, 960)).save(image)
    result = extent()
    save_extend(result, image)
    assert load_extend(image) == result
    assert load_extend(tmp_path / "absent.png") is None
    sidecar = image.with_suffix(".md").read_text()
    assert "- Seed: 42" in sidecar
    assert "- Output: 1280 x 960 px" in sidecar
    assert "- Peak VRAM: 30.50 GB" in sidecar
    assert "`steps=20`" in sidecar


def test_upscale_result_round_trip(tmp_path: Path) -> None:
    image = tmp_path / "IMG_0001.png"
    Image.new("RGB", (2560, 1920)).save(image)
    result = UpscaleResult(
        image=str(image),
        source="data/processed/x/4x3/qwen/IMG_8564.png",
        upscaler="seedvr2-3b",
        model="SeedVR2 3B",
        weights="Comfy-Org/SeedVR2",
        licence="Apache-2.0",
        prompt="",
        seed=42,
        settings={"tile": 512, "target": [2560, 1920]},
        target_width=2560,
        target_height=1920,
        render_width=2560,
        render_height=1920,
        width=2560,
        height=1920,
        ratio=1.3333,
        extender=extent(),
        gpu="RTX PRO 6000 Blackwell",
        seconds=80.0,
        peak_vram_gb=18.0,
        notes="one step",
    )
    save_upscale(result, image)
    restored = load_upscale(image)
    assert restored == result
    assert restored is not None and restored.extender.model == "Qwen-Image"
    sidecar = image.with_suffix(".md").read_text()
    assert "Extender: Qwen-Image" in sidecar and "Upscaler: SeedVR2 3B" in sidecar
    assert "Target size: 2560 x 1920 px" in sidecar


def test_contact_sheet_writes_a_png_and_names_every_tile(tmp_path: Path) -> None:
    tile = tmp_path / "tile.png"
    Image.new("RGB", (100, 75), (10, 20, 30)).save(tile)
    sheet = contact_sheet(
        [[Tile(tile, "source"), Tile(None, "none")], [Tile(None, "qwen"), Tile(tile, "qwen + none")]],
        tmp_path / "grid.png",
    )
    with Image.open(sheet) as opened:
        assert opened.width == 2 * 560  # two equal columns
    index = (tmp_path / "grid.md").read_text()
    assert "| 1 | 1 | source |" in index
    assert "| 2 | 2 | qwen + none |" in index


def test_setup_load_keeps_only_the_gpu_uuid_and_paths(tmp_path: Path) -> None:
    path = tmp_path / "setup-extender.json"
    path.write_text(
        json.dumps(
            {
                "gpu": "GPU-a44e514a-aa5b-2844-35f1-4be28e1921e5 index 1 RTX PRO 6000",
                "port": 8189,
                "launch_command": "true",
                "stop_command": "true",
                "io_dirs": {"input": "/tmp/in", "output": "/tmp/out", "temp": "/tmp/tmp"},
                "graphs": {"seedvr2": "/tmp/seedvr2.json"},
                "paths": {"hypir_base_model": "/models/sd21"},
            }
        )
    )
    setup = Setup.load(path)
    assert setup.gpu == "GPU-a44e514a-aa5b-2844-35f1-4be28e1921e5"
    assert setup.port == 8189
    assert setup.io_dirs["input"] == Path("/tmp/in")
    assert setup.paths["hypir_base_model"] == "/models/sd21"


def test_every_graph_marker_is_filled_by_the_registry() -> None:
    """A graph that asks for a marker no setting provides would fail only at render time."""
    fixed = {
        "IMAGE", "FILENAME_PREFIX", "PROMPT", "NEGATIVE_PROMPT", "SEED",
        "PAD_LEFT", "PAD_RIGHT", "PAD_TOP", "PAD_BOTTOM", "FEATHER",
        "WIDTH", "HEIGHT", "UNET",
    }
    graphs = Path(registry.__file__).parent / "graphs"
    for entry in registry.EXTENDERS:
        text = (graphs / f"{entry.graph}.json").read_text()
        markers = set(re.findall(r"\{\{[A-Z_]+\}\}", text))
        provided = {f"{{{{{name}}}}}" for name in fixed}
        provided |= {f"{{{{{key.upper()}}}}}" for key in entry.settings}
        assert not markers - provided, f"{entry.name}: {sorted(markers - provided)}"
