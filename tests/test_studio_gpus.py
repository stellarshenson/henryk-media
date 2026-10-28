"""Tests for the studio's automatic choice and the memory fit check."""

from conftest import FAKE_SMI, OUTPAINT, VIDEO, fake_gpus

from henryk_media.studio.gpus import H3_GB, KLEIN_GB, choose, gb, need_gb, parse

GPU_1 = "GPU-11111111-1111-4111-8111-111111111111"
GPU_2 = "GPU-22222222-2222-4222-8222-222222222222"
# 25.2, 96.0 and 72.0 GB free on the 25.7, 102.6 and 77.0 GB cards
ROWS = parse(FAKE_SMI)


def test_gpu_list_api_is_gone(make_studio, serve) -> None:
    client = serve(make_studio())
    assert client.get("/api/gpus")[0] == 404  # the page fetches no GPU data


def test_choice_takes_the_largest_gpu_that_fits_and_has_room() -> None:
    assert choose(ROWS, 68.823).uuid == GPU_1  # the 102.6 GB card, not the 77.0 GB one
    busy = parse(FAKE_SMI.replace("97887, 96000, 1100", "97887, 60000, 37887"))  # 60 GB free
    assert choose(busy, 68.823).uuid == GPU_2  # the next one when the largest is busy
    assert choose(ROWS, 21.317).uuid == GPU_1  # the largest that fits, not the roomiest
    assert choose(ROWS, 200) is None  # above every total


def test_choice_counts_the_servers_own_memory_as_free() -> None:
    busy = parse(FAKE_SMI.replace("97887, 96000, 1100", "97887, 60000, 37887"))
    assert choose(busy, 68.823, GPU_1, 40000).uuid == GPU_1  # 60 + 40 GB held by the server
    assert choose(busy, 68.823, GPU_2, 40000).uuid == GPU_2  # held memory on another card


def test_choice_returns_none_when_no_gpu_has_room() -> None:
    full = FAKE_SMI.replace("24467, 24015, 0", "24467, 0, 24467")
    full = full.replace("97887, 96000, 1100", "97887, 0, 97887")
    full = full.replace("73415, 72000, 900", "73415, 0, 73415")
    assert choose(parse(full), 68.823) is None


def test_job_above_every_gpu_total_is_refused_with_a_plain_warning(
    make_studio, serve, fake_server
) -> None:
    client = serve(make_studio())
    uhd = {**VIDEO, "ref": "2/4x3/IMG_0001.png", "resolution": 2160}  # 2880x2160, 10 s
    status, body = client.post("/api/jobs", uhd)
    assert status == 400
    assert "needs 119.433 GB" in body["error"]
    assert "the workstation cannot provide it" in body["error"]
    for hidden in ("NVIDIA", "GPU", "in total", "GB free", "102.6"):
        assert hidden not in body["error"], body["error"]
    assert fake_server.instances == []
    assert client.get("/api/jobs")[1]["jobs"] == []
    held = FAKE_SMI.replace("24467, 24015, 0", "24467, 0, 24467")
    held = held.replace("97887, 96000, 1100", "97887, 0, 97887")
    held = held.replace("73415, 72000, 900", "73415, 0, 73415")
    client = serve(make_studio(gpus=fake_gpus(held)))
    assert client.post("/api/jobs", VIDEO)[0] == 201  # a total holds it: accepted with no free


def test_job_that_finds_no_room_fails_with_a_plain_warning(
    make_studio, serve, fake_server
) -> None:
    no_room = FAKE_SMI.replace("24467, 24015, 0", "24467, 1000, 23467")
    no_room = no_room.replace("97887, 96000, 1100", "97887, 1000, 96887")
    no_room = no_room.replace("73415, 72000, 900", "73415, 1000, 72415")
    client = serve(make_studio(gpus=fake_gpus(no_room)))
    status, reply = client.post("/api/jobs", OUTPAINT)
    assert status == 201, reply  # every total holds it; the free memory is checked at start
    job = client.wait(reply["job"]["id"], "failed")
    assert "21.317 GB" in job["error"]
    assert "the workstation cannot provide it" in job["error"]
    for hidden in ("NVIDIA", "GPU", "GB free", "1.0"):
        assert hidden not in job["error"], job["error"]
    assert fake_server.instances == []


def test_start_choice_counts_the_servers_own_memory(make_studio, serve, fake_server) -> None:
    texts = [FAKE_SMI]
    client = serve(make_studio(gpus=lambda: parse(texts[0])))
    frame = client.post("/api/jobs", OUTPAINT)[1]["job"]
    client.wait(frame["id"], "done")
    # 60 GB free plus the 37,387 MiB the FakeServer holds (used 37,887 - baseline 500)
    texts[0] = FAKE_SMI.replace("97887, 96000, 1100", "97887, 60000, 37887")
    video = client.post("/api/jobs", VIDEO)[1]["job"]
    done = client.wait(video["id"], "done", "failed")
    assert done["gpu"]["uuid"] == GPU_1, done
    assert len(fake_server.instances) == 1  # the server on GPU 1 was reused


def test_memory_table_covers_every_option() -> None:
    assert len(H3_GB) == 6
    for (size, seconds), peak in H3_GB.items():  # the estimate meets every recorded row
        render = [int(side) for side in size.split("x")]
        assert need_gb("video", {"duration": seconds, "render": render}) == peak
    assert need_gb("video", {"duration": 10, "render": [1280, 736]}) == 70.967  # 16:9 HD
    assert round(gb(ROWS[2].total_mib), 1) == 77.0


def test_klein_estimate_meets_every_recorded_row() -> None:
    sizes = [(1280, 960), (1080, 1080), (1920, 1080), (3840, 2160)]
    assert sorted(width * height for width, height in sizes) == sorted(KLEIN_GB)
    for width, height in sizes:
        estimate = need_gb("outpaint", {"size": [width, height]})
        assert abs(estimate - KLEIN_GB[width * height]) <= 0.5, (width, height, estimate)
    assert need_gb("outpaint", {"size": [1280, 720]}) == KLEIN_GB[1280 * 960]  # never below it


def test_klein_frame_fit_follows_the_frame_size(make_studio, serve) -> None:
    client = serve(make_studio(gpus=fake_gpus(FAKE_SMI.splitlines()[0] + "\n")))  # only 25.7 GB
    uhd = {**OUTPAINT, "resolution": 2160}  # the portrait IMG_0001 outpainted sideways
    status, body = client.post("/api/jobs", uhd)
    assert status == 400
    assert "needs 27.48 GB" in body["error"]
    assert "the workstation cannot provide it" in body["error"]
    assert "25.7" not in body["error"] and "NVIDIA" not in body["error"]
    assert client.post("/api/jobs", {**uhd, "resolution": 1080})[0] == 201  # 22.054 GB
    crop = {**uhd, "ref": "0/WIDE_0002.jpg", "aspect": "4x3"}  # 2880x2160: a crop, no fit
    status, reply = client.post("/api/jobs", crop)
    assert (status, reply["job"]["params"]["frame"]) == (201, "cropped"), reply
