"""Tests for the studio's GPU list and the memory fit check."""

from conftest import FAKE_SMI, OUTPAINT, VIDEO, fake_gpus

from henryk_media.studio.gpus import H3_GB, OUTPAINT_GB, gb, need_gb, parse


def test_api_lists_every_gpu_nvidia_smi_reports(make_studio, serve) -> None:
    client = serve(make_studio())
    status, body = client.get("/api/gpus")
    assert status == 200
    assert [row["index"] for row in body["gpus"]] == [0, 1, 2]
    assert body["gpus"][0] == {
        "index": 0,
        "uuid": "GPU-00000000-0000-4000-8000-000000000000",
        "name": "NVIDIA RTX PRO 4000 Blackwell",
        "total_gb": 25.7,
        "free_gb": 25.2,
    }
    assert body["gpus"][1]["name"] == "NVIDIA RTX PRO 6000 Blackwell Max-Q Workstation Edition"
    assert body["selected"] is None
    assert client.post("/api/gpu", {"index": 2}) == (200, {"selected": 2})
    assert client.get("/api/gpus")[1]["selected"] == 2
    assert client.post("/api/gpu", {"index": 7})[0] == 400
    assert client.post("/api/gpu", {"index": "2"})[0] == 400


def test_job_above_the_gpu_total_is_refused_naming_both_gb(
    make_studio, serve, fake_server
) -> None:
    client = serve(make_studio())
    client.post("/api/gpu", {"index": 0})
    status, body = client.post("/api/jobs", VIDEO)
    assert status == 400
    assert "69.55 GB" in body["error"] and "25.7 GB in total" in body["error"]
    assert "GPU 0 NVIDIA RTX PRO 4000 Blackwell" in body["error"]
    assert fake_server.instances == []
    assert client.get("/api/jobs")[1]["jobs"] == []


def test_job_above_the_free_memory_is_refused_without_a_launch(
    make_studio, serve, fake_server
) -> None:
    busy = FAKE_SMI.replace("24467, 24015, 0", "24467, 1907, 22560")  # 2.0 GB free
    client = serve(make_studio(gpus=fake_gpus(busy)))
    client.post("/api/gpu", {"index": 0})
    status, body = client.post("/api/jobs", OUTPAINT)
    assert status == 409
    assert "21.317 GB" in body["error"] and "2.0 GB available" in body["error"]
    assert fake_server.instances == []
    assert client.get("/api/jobs")[1]["jobs"] == []


def test_memory_table_covers_every_option() -> None:
    assert need_gb("outpaint", {"aspect": "1x1", "width": 1920}) == OUTPAINT_GB
    assert len(H3_GB) == 6
    assert need_gb("video", {"resolution": "480x320", "duration": 5}) == 63.79
    assert round(gb(parse(FAKE_SMI)[2].total_mib), 1) == 77.0
