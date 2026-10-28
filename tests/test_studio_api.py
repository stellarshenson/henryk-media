"""Tests for the studio's picker, uploads, path guard, narrow-photo refusal and saved prompts."""

import http.client
import io
from urllib.parse import quote, urlsplit

from conftest import OUTPAINT, VIDEO, noise


def png_bytes() -> bytes:
    buffer = io.BytesIO()
    noise((40, 30)).save(buffer, "PNG")
    return buffer.getvalue()


def test_picker_lists_names_without_thumbnails(make_studio, serve) -> None:
    status, body = serve(make_studio()).get("/api/images")
    assert status == 200
    assert body["images"] == [
        {"ref": "2/4x3/IMG_0001.png", "label": "extended/4x3/IMG_0001.png"},
        {"ref": "1/IMG_0003.png", "label": "images/IMG_0003.png"},
        {"ref": "0/IMG_0001.jpg", "label": "raw/IMG_0001.jpg"},
        {"ref": "0/WIDE_0002.jpg", "label": "raw/WIDE_0002.jpg"},
    ]  # no hidden file, no link out of the tree, no URL field


def test_upload_is_stored_and_listed(make_studio, serve, tmp_path) -> None:
    client = serve(make_studio())
    data = png_bytes()
    status, body = client.call("POST", "/api/uploads?name=my%20photo!.PNG", data, "image/png")
    assert status == 201
    assert body == {"ref": "3/myphoto.png", "label": "uploads/myphoto.png"}
    assert (tmp_path / "state/uploads/myphoto.png").read_bytes() == data
    assert body in client.get("/api/images")[1]["images"]
    assert client.get(f"/api/file?ref={quote(body['ref'])}") == (200, data)


def test_upload_under_a_used_name_with_other_bytes_is_refused(
    make_studio, serve, tmp_path
) -> None:
    client = serve(make_studio())
    first = png_bytes()
    buffer = io.BytesIO()
    noise((40, 30), seed=1).save(buffer, "PNG")
    assert client.call("POST", "/api/uploads?name=x.png", first, "image/png")[0] == 201
    status, body = client.call("POST", "/api/uploads?name=x.png", buffer.getvalue(), "image/png")
    assert status == 409, body
    assert (tmp_path / "state/uploads/x.png").read_bytes() == first


def test_invalid_or_oversized_upload_is_refused_and_writes_nothing(
    make_studio, serve, tmp_path
) -> None:
    client = serve(make_studio())
    uploads = tmp_path / "state/uploads"
    for data in (b"not an image\n", png_bytes()[:-40]):  # text, and a truncated PNG
        status, body = client.call("POST", "/api/uploads?name=x.png", data, "image/png")
        assert status == 400, body
    address = urlsplit(client.url)
    connection = http.client.HTTPConnection(address.hostname, address.port, timeout=10)
    connection.putrequest("POST", "/api/uploads?name=big.png")
    connection.putheader("Content-Type", "image/png")
    connection.putheader("Content-Length", str(51_000_000))
    connection.endheaders()  # the body is never sent: the server refuses on the header
    response = connection.getresponse()
    assert response.status == 400
    connection.close()
    assert list(uploads.iterdir()) == []


def test_paths_outside_the_roots_return_404(make_studio, serve) -> None:
    client = serve(make_studio())
    for ref in (
        "0/../../.env",
        "0/../../../../../../etc/passwd",
        "0//etc/passwd",
        "/etc/passwd",
        "0/escape.png",  # a symlink out of the root
        "0/.hidden.png",
        "9/IMG_0001.jpg",
        "x/IMG_0001.jpg",
        "",
    ):
        status, body = client.get(f"/api/file?ref={quote(ref)}")
        assert status == 404, ref
        assert body == {"error": "not found"}
    assert client.get("/api/prompts?ref=0/escape.png&kind=video")[0] == 404
    assert client.get("/static/..%2F__init__.py")[0] == 404
    assert client.get("/api/file?ref=0/IMG_0001.jpg")[0] == 200


def test_photo_already_wide_is_refused(make_studio, serve) -> None:
    client = serve(make_studio())
    client.post("/api/gpu", {"index": 1})
    status, body = client.post(
        "/api/jobs", {**OUTPAINT, "ref": "0/WIDE_0002.jpg", "aspect": "4x3"}
    )
    assert status == 400
    assert body["error"] == (
        "the photo (1600x900) is already as wide as 4x3 or wider; nothing is left to extend"
    )
    assert client.post("/api/jobs", {**OUTPAINT, "ref": "0/WIDE_0002.jpg"})[0] == 400  # 16:9
    assert client.get("/api/jobs")[1]["jobs"] == []


def test_submitted_prompts_are_saved_per_image_and_kind(make_studio, serve) -> None:
    client = serve(make_studio())
    client.post("/api/gpu", {"index": 1})
    fields = {
        "action": "he waves",
        "camera": "Static Shot",
        "hold": "",
        "soundscape": "",
        "music": "",
    }
    video = {**VIDEO, "prompt": "final text", "fields": fields}
    assert client.post("/api/jobs", video)[0] == 201
    assert client.post("/api/jobs", {**OUTPAINT, "negative_prompt": "", "cfg": 2.0})[0] == 201

    saved = client.get("/api/prompts?ref=0/IMG_0001.jpg&kind=video")[1]["saved"]
    assert saved == {key: value for key, value in video.items() if key not in ("kind", "ref")}
    saved = client.get("/api/prompts?ref=0/IMG_0001.jpg&kind=outpaint")[1]["saved"]
    assert saved["negative_prompt"] == "" and saved["cfg"] == 2.0
    assert client.get("/api/prompts?ref=0/WIDE_0002.jpg&kind=video")[1]["saved"] is None
    assert client.get("/api/prompts?ref=0/IMG_0001.jpg&kind=image")[0] == 400
