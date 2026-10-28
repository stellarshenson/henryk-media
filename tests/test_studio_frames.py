"""Tests for the frame step, the outpaint frame sizes and the video sizes and lengths."""

import io
from types import SimpleNamespace

from conftest import FAKE_SMI, OUTPAINT, FakeGate, fake_gpus, noise
from PIL import Image, ImageChops, ImageDraw, ImageOps
import pytest

from henryk_media.imaging.composite import RESAMPLE, Geometry, interior_matches
from henryk_media.imaging.extender import ASPECTS, FEATHER
from henryk_media.studio.comfy import comfy_setup
from henryk_media.studio.generators import (
    DURATIONS,
    PRESETS,
    Outpaint,
    Video,
    clip_size,
    frame_step,
    h3_size,
    preset_size,
    window_left,
)

SIZES = {  # HD, Full HD, 2K, UHD 4K
    "1x1": [(720, 720), (1080, 1080), (1440, 1440), (2160, 2160)],
    "4x3": [(960, 720), (1440, 1080), (1920, 1440), (2880, 2160)],
    "3x2": [(1080, 720), (1620, 1080), (2160, 1440), (3240, 2160)],
    "16x9": [(1280, 720), (1920, 1080), (2560, 1440), (3840, 2160)],
}


def test_outpaint_frames_reach_each_aspect() -> None:
    photo = (600, 800)  # 3:4
    assert list(ASPECTS) == ["1x1", "4x3", "3x2", "16x9"]
    for ratio in ASPECTS.values():
        for lines in PRESETS:
            geometry = Geometry.for_aspect(photo, ratio, FEATHER, *preset_size(ratio, lines))
            assert geometry.width / geometry.height == pytest.approx(ratio, rel=0.002)
            assert geometry.photo_size(photo)[0] < geometry.width  # both sides are extended
            assert geometry.pad_left > 0 and geometry.pad_right > 0


def test_frame_and_clip_sizes_follow_the_preset_ladder() -> None:
    assert PRESETS == {720: "HD", 1080: "Full HD", 1440: "2K", 2160: "UHD 4K"}
    for aspect, sizes in SIZES.items():
        for lines, size in zip(PRESETS, sizes, strict=True):
            assert preset_size(ASPECTS[aspect], lines) == size  # the frame
            geometry = Geometry.for_aspect((600, 800), ASPECTS[aspect], FEATHER, *size)
            assert (geometry.width, geometry.height) == size
            extended = geometry.extended((600, 800))  # the Klein canvas, on the 16 px patch
            assert extended[0] % 16 == 0 and extended[1] % 16 == 0
            for frame in sizes:  # a clip of any frame of the aspect
                assert clip_size(frame, lines) == size
            assert clip_size(size[::-1], lines) == size[::-1]  # an upright source stays upright
            render = h3_size(size)
            assert render[0] % 32 == 0 and render[1] % 32 == 0
            assert size[0] <= render[0] < size[0] + 32 and size[1] <= render[1] < size[1] + 32
    assert h3_size((1280, 720)) == (1280, 736)


@pytest.mark.parametrize(
    ("source", "lines", "size", "render"),
    [
        ((1280, 720), 720, (1280, 720), (1280, 736)),
        ((600, 800), 720, (720, 960), (736, 960)),
        ((1620, 1080), 1080, (1620, 1080), (1632, 1088)),
        ((700, 700), 1440, (1440, 1440), (1440, 1440)),
    ],
)
def test_clip_renders_on_the_32_step_and_crops_to_the_preset(
    tmp_path, fake_server, fake_film, trashed, source, lines, size, render
) -> None:
    photo = tmp_path / "IMG_0001.png"
    noise(source).save(photo)
    server = fake_server(comfy_setup("GPU-test", 8600), lambda event: None)
    for seconds, (length, frames) in DURATIONS.items():
        params = {"prompt": "p", "duration": seconds, "resolution": lines, "seed": 7}
        params |= {"size": list(clip_size(source, lines)), "render": list(h3_size(size))}
        folder = tmp_path / f"job-{seconds}"
        job = SimpleNamespace(path=str(photo), params=params)
        assert Video().run(job, server, folder) == folder / "IMG_0001.mp4"
        node, crop = server.graphs[-1]["6"]["inputs"], server.graphs[-1]["16"]["inputs"]
        assert (node["width"], node["height"], node["length"]) == (*render, length)
        assert (crop["width"], crop["height"]) == size  # the clip is the exact preset size
        assert (crop["x"], crop["y"]) == ((render[0] - size[0]) // 2, (render[1] - size[1]) // 2)
        assert server.graphs[-1]["14"]["inputs"]["images"] == ["16", 0]
        with Image.open(folder / "input/IMG_0001.png") as fed:
            assert fed.size == render  # H3 receives its canvas size and stretches nothing
        assert server.graphs[-1]["7"]["inputs"]["noise_seed"] == 7
        assert fake_film[-1][3] == frames
    assert [seconds for seconds in DURATIONS] == [5, 6, 10]
    assert [length for length, _ in DURATIONS.values()] == [124, 158, 243]


def test_frame_fed_to_h3_keeps_its_aspect(tmp_path, fake_server, fake_film, trashed) -> None:
    photo = tmp_path / "IMG_0001.png"
    disc = Image.new("RGB", (1280, 720))
    ImageDraw.Draw(disc).ellipse((490, 210, 790, 510), fill="white")  # 300 px round
    disc.save(photo)
    params = {"prompt": "p", "duration": 5, "resolution": 720, "seed": 7}
    params |= {"size": [1280, 720], "render": [1280, 736]}  # 736 / 720 would stretch 2.2 %
    server = fake_server(comfy_setup("GPU-test", 8600), lambda event: None)
    Video().run(SimpleNamespace(path=str(photo), params=params), server, tmp_path / "job")
    with Image.open(tmp_path / "job/input/IMG_0001.png") as fed:
        left, top, right, bottom = fed.convert("L").point(lambda v: 255 * (v > 127)).getbbox()
    assert abs((right - left) - (bottom - top)) <= 1  # still round: one scale for both sides
    assert right - left == pytest.approx(300 * 736 / 720, abs=1.5)


@pytest.mark.parametrize(
    ("size", "aspect", "step"),
    [
        ((450, 800), "4x3", "outpainted sideways"),  # 9:16
        ((1600, 900), "4x3", "cropped"),  # 16:9
        ((800, 600), "4x3", "scaled"),
        ((796, 600), "4x3", "scaled"),  # 0.5 percent narrower
        ((784, 600), "4x3", "outpainted sideways"),  # 2 percent narrower
        ((900, 600), "3x2", "scaled"),
        ((1600, 900), "16x9", "scaled"),
        ((800, 600), "1x1", "outpainted above and below"),
        ((600, 800), "1x1", "outpainted sideways"),
        ((604, 600), "1x1", "scaled"),
    ],
)
def test_frame_step_outpaints_only_the_larger_dimension(size, aspect, step) -> None:
    assert frame_step(size, aspect) == step


def test_crop_window_lies_over_the_people_and_is_clamped() -> None:
    face, person = "face", "person"
    assert window_left(1600, 1200, []) == 200  # nothing detected: centred
    found = [
        (person, "person", 0.9, (850, 50, 1050, 850)),
        (face, "face", 0.8, (900, 100, 1000, 200)),
    ]
    assert window_left(1600, 1200, found) == 350  # centred on the union
    assert window_left(1600, 1200, [(person, "person", 0.9, (520, 50, 680, 850))]) == 0
    wide = [
        (person, "person", 0.9, (50, 0, 1550, 900)),
        (face, "face", 0.8, (100, 100, 200, 200)),
        (face, "face", 0.8, (1300, 100, 1500, 300)),
    ]
    assert window_left(1600, 1200, wide) == 400  # the union is wider: the largest face, clamped
    assert window_left(1600, 1200, wide[:2]) == 0


def frame_job(client, image_tree, size, aspect) -> tuple[dict, str, Image.Image]:
    """Queue one outpaint of a synthetic photo of ``size``; return the job, sidecar and result."""
    noise(size, 3).save(image_tree / "data/raw/PHOTO.png")
    status, reply = client.post("/api/jobs", {**OUTPAINT, "ref": "0/PHOTO.png", "aspect": aspect})
    assert status == 201, reply
    job = client.wait(reply["job"]["id"], "done", "failed")
    assert job["state"] == "done", job
    sidecar = client.get(f"/api/file?ref={job['sidecar']['ref']}")[1].decode()
    result = Image.open(io.BytesIO(client.get(f"/api/file?ref={job['result']['ref']}")[1]))
    return job, sidecar, result.convert("RGB")


@pytest.mark.parametrize(
    ("size", "aspect", "frame"),
    [((450, 800), "4x3", (960, 720)), ((600, 800), "1x1", (720, 720))],
)
def test_narrower_photo_is_outpainted_sideways(
    make_studio, serve, image_tree, fake_server, size, aspect, frame
) -> None:
    client = serve(make_studio({"outpaint": Outpaint(FakeGate()), "video": Video()}))
    job, sidecar, result = frame_job(client, image_tree, size, aspect)
    assert job["params"]["frame"] == "outpainted sideways"
    pads = fake_server.instances[0].graphs[0]["2"]["inputs"]  # the generator ran
    assert pads["left"] > 0 and pads["top"] == 0
    assert result.size == frame
    assert sidecar.startswith("Frame step: outpainted sideways\n")
    assert "- Studio GPU: index 1" in sidecar


def test_landscape_photo_at_square_is_outpainted_above_and_below(
    make_studio, serve, image_tree, fake_server, tmp_path
) -> None:
    client = serve(make_studio({"outpaint": Outpaint(FakeGate()), "video": Video()}))
    job, sidecar, result = frame_job(client, image_tree, (800, 600), "1x1")
    assert job["params"]["frame"] == "outpainted above and below"
    pads = fake_server.instances[0].graphs[0]["2"]["inputs"]
    assert (pads["left"], pads["top"], pads["bottom"]) == (0, 90, 90)
    assert result.size == (720, 720)
    with Image.open(tmp_path / "state/jobs" / job["id"] / "input/PHOTO.png") as opened:
        photo = opened.convert("RGB").resize((720, 540), RESAMPLE)
    assert interior_matches(result, photo, (0, 90), FEATHER)  # the photo's pixels are kept
    assert sidecar.startswith("Frame step: outpainted above and below\n")
    assert "panels y 0-90 and y 630-720" in sidecar


def test_wider_photo_is_cropped_over_the_people_without_a_model(
    make_studio, serve, image_tree, fake_server, tmp_path
) -> None:
    busy = FAKE_SMI.replace("24467, 24015, 0", "24467, 1907, 22560")  # 2.0 GB free
    people = [("person", "person", 0.9, (850.0, 50.0, 1050.0, 850.0))]
    client = serve(
        make_studio(
            {"outpaint": Outpaint(FakeGate(people=people)), "video": Video()}, gpus=fake_gpus(busy)
        )
    )
    job, sidecar, result = frame_job(client, image_tree, (1600, 900), "4x3")
    assert job["params"]["frame"] == "cropped"
    assert fake_server.instances == []  # no server, no generative model, the fit check passed
    with Image.open(tmp_path / "state/jobs" / job["id"] / "input/PHOTO.png") as opened:
        photo = opened.convert("RGB")
    expected = photo.resize((960, 720), RESAMPLE, box=(350, 0, 1550, 900))
    assert result.tobytes() == expected.tobytes()
    assert sidecar.startswith(
        "Frame step: cropped sideways from 1600x900 over the detected people, "
        "no generative model\n"
    )
    assert "- Crop window: x 350-1550 of 1600 px\n" in sidecar
    assert "- Studio GPU" not in sidecar

    client = serve(make_studio({"outpaint": Outpaint(FakeGate()), "video": Video()}))
    job, sidecar, result = frame_job(client, image_tree, (1600, 900), "4x3")
    assert sidecar.startswith(
        "Frame step: cropped sideways from 1600x900 centred, no person detected, "
        "no generative model\n"
    )
    assert "- Crop window: x 200-1400 of 1600 px\n" in sidecar
    assert fake_server.instances == []


@pytest.mark.parametrize("size", [(800, 600), (796, 600)])
def test_photo_at_the_aspect_is_scaled_without_a_model(
    make_studio, serve, image_tree, fake_server, tmp_path, size
) -> None:
    client = serve(make_studio({"outpaint": Outpaint(FakeGate()), "video": Video()}))
    job, sidecar, result = frame_job(client, image_tree, size, "4x3")
    assert job["params"]["frame"] == "scaled"
    assert fake_server.instances == []
    with Image.open(tmp_path / "state/jobs" / job["id"] / "input/PHOTO.png") as opened:
        expected = ImageOps.fit(opened.convert("RGB"), (960, 720), RESAMPLE)
    assert result.tobytes() == expected.tobytes()
    assert sidecar.startswith(
        "Frame step: scaled, the photo already had the 4:3 aspect, no generative model\n"
    )


def test_crop_and_scale_run_with_no_gpu(make_studio, serve, fake_server) -> None:
    client = serve(make_studio({"outpaint": Outpaint(FakeGate()), "video": Video()}))
    wide = {**OUTPAINT, "ref": "0/WIDE_0002.jpg"}  # 1600x900
    for aspect, step in (("4x3", "cropped"), ("16x9", "scaled")):
        status, reply = client.post("/api/jobs", {**wide, "aspect": aspect})
        assert status == 201, reply
        job = client.wait(reply["job"]["id"], "done", "failed")
        assert (job["state"], job["params"]["frame"], job["gpu"]) == ("done", step, None), job
    assert fake_server.instances == []
    assert len(client.get("/api/jobs")[1]["jobs"]) == 1  # the scale trashed the crop: latest only


@pytest.mark.parametrize(("lines", "copy"), [(2160, (2880, 2160)), (1080, (2048, 1536))])
def test_uhd_frame_takes_the_original_pixels(tmp_path, fake_server, trashed, lines, copy) -> None:
    photo = tmp_path / "PHOTO.jpg"
    noise((4000, 3000)).save(photo)
    size = preset_size(ASPECTS["16x9"], lines)
    params = {**OUTPAINT, "size": list(size), "frame": "outpainted sideways"}
    server = fake_server(comfy_setup("GPU-test", 8600), lambda event: None)
    result = Outpaint(FakeGate()).run(
        SimpleNamespace(path=str(photo), params=params), server, tmp_path / "job"
    )
    with Image.open(tmp_path / "job/input/PHOTO.png") as opened:
        working = opened.convert("RGB")
    assert working.size == copy  # Full HD keeps the 2048 px copy
    geometry = Geometry.for_aspect(working.size, ASPECTS["16x9"], FEATHER, *size)
    band = geometry.photo_size(working.size)
    assert band == (copy if lines == 2160 else (1440, 1080))  # UHD: the copy, not enlarged
    with Image.open(result) as opened:
        frame = opened.convert("RGB")
    assert frame.size == size
    assert interior_matches(
        frame, geometry.resized(working), geometry.origin(working.size), FEATHER
    )


def test_uhd_clip_is_fitted_from_the_original_pixels(
    tmp_path, fake_server, fake_film, trashed
) -> None:
    photo = noise((3840, 2160))
    photo.save(tmp_path / "IMG_0001.png")
    size = preset_size(ASPECTS["16x9"], 2160)
    render = h3_size(size)
    params = {"prompt": "p", "duration": 5, "resolution": 2160, "seed": 7}
    params |= {"size": list(size), "render": list(render)}
    server = fake_server(comfy_setup("GPU-test", 8600), lambda event: None)
    job = SimpleNamespace(path=str(tmp_path / "IMG_0001.png"), params=params)
    Video().run(job, server, tmp_path / "job")
    with Image.open(tmp_path / "job/input/IMG_0001.png") as fed:
        received = fed.convert("RGB")
    assert received.size == render  # H3 receives its canvas size
    expected = ImageOps.fit(photo, render, RESAMPLE)  # the source, not a 2048 px copy
    assert ImageChops.difference(received, expected).getbbox() is None
