"""Tests for the outpaint frame sizes and the video sizes and lengths the studio offers."""

from types import SimpleNamespace

from conftest import noise
import pytest

from henryk_media.imaging.composite import Geometry
from henryk_media.imaging.extender import ASPECTS, FEATHER
from henryk_media.studio.app import WIDTHS
from henryk_media.studio.comfy import comfy_setup
from henryk_media.studio.generators import DURATIONS, Video

SIZES = {
    "1x1": [(1024, 1024), (1280, 1280), (1536, 1536), (1920, 1920)],
    "4x3": [(1024, 768), (1280, 960), (1536, 1152), (1920, 1440)],
    "3x2": [(1024, 688), (1280, 848), (1536, 1024), (1920, 1280)],
    "16x9": [(1024, 576), (1280, 720), (1536, 864), (1920, 1088)],
}


def test_outpaint_frames_reach_each_aspect() -> None:
    photo = (600, 800)  # 3:4
    assert list(ASPECTS) == ["1x1", "4x3", "3x2", "16x9"]
    for aspect, ratio in ASPECTS.items():
        for width in WIDTHS:
            geometry = Geometry.for_aspect(photo, ratio, FEATHER, width)
            assert geometry.width / geometry.height == pytest.approx(ratio, rel=0.01)
            assert geometry.photo_size(photo)[0] < geometry.width  # both sides are extended
            assert geometry.pad_left > 0 and geometry.pad_right > 0


def test_outpaint_sizes_are_multiples_of_16_at_every_width() -> None:
    assert WIDTHS == (1024, 1280, 1536, 1920)
    for aspect, sizes in SIZES.items():
        for width, size in zip(WIDTHS, sizes, strict=True):
            geometry = Geometry.for_aspect((600, 800), ASPECTS[aspect], FEATHER, width)
            assert (geometry.width, geometry.height) == size
            assert geometry.width % 16 == 0 and geometry.height % 16 == 0
            assert geometry.pad_bottom == 0
            assert geometry.extended((600, 800)) == size  # no stride padding to crop


@pytest.mark.parametrize(
    ("source", "resolution", "size"),
    [
        ((600, 800), "1024x768", (768, 1024)),
        ((800, 600), "1024x768", (1024, 768)),
        ((700, 700), "1024x768", (1024, 1024)),
        ((600, 800), "480x320", (352, 480)),
        ((1280, 720), "1024x768", (1024, 576)),
    ],
)
def test_video_size_follows_the_source_orientation_and_duration(
    tmp_path, fake_server, fake_film, trashed, source, resolution, size
) -> None:
    photo = tmp_path / "IMG_0001.png"
    noise(source).save(photo)
    server = fake_server(comfy_setup("GPU-test", 8600), lambda event: None)
    for seconds, (length, frames) in DURATIONS.items():
        job = SimpleNamespace(
            path=str(photo),
            params={"prompt": "p", "duration": seconds, "resolution": resolution, "seed": 7},
        )
        folder = tmp_path / f"job-{seconds}"
        assert Video().run(job, server, folder) == folder / "IMG_0001.mp4"
        node = server.graphs[-1]["6"]["inputs"]
        assert (node["width"], node["height"], node["length"]) == (*size, length)
        assert server.graphs[-1]["7"]["inputs"]["noise_seed"] == 7
        assert fake_film[-1][3] == frames
    assert [seconds for seconds in DURATIONS] == [5, 6, 10]
    assert [length for length, _ in DURATIONS.values()] == [124, 158, 243]
