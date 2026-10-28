"""The pre-commit and pre-push hooks refuse originals, media outside .images_readme/, content
filters, embedded media, archives and notebook payloads."""

import hashlib
import json
from pathlib import Path
import random
import shutil
import subprocess
import zipfile

from PIL import Image, ImageDraw
import pytest

ROOT = Path(__file__).resolve().parents[1]
SHOWCASE = ROOT / "data" / "external" / "showcase"
SHOWCASE_FILES = ("IMG_0020.jpeg", "IMG_0020-frame-16x9-fullhd.png", "IMG_0020-clip-hd-5s.mp4")


@pytest.fixture
def repo(tmp_path):
    """A temporary git repository with the project hooks, .gitignore and a link to the venv."""
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    shutil.copytree(ROOT / ".githooks", tmp_path / ".githooks")
    shutil.copy(ROOT / ".gitignore", tmp_path / ".gitignore")
    (tmp_path / ".venv").symlink_to(ROOT / ".venv")
    for key, value in [
        ("core.hooksPath", ".githooks"),
        ("user.name", "test"),
        ("user.email", "test@example.com"),
        ("commit.gpgsign", "false"),
    ]:
        subprocess.run(["git", "-C", str(tmp_path), "config", key, value], check=True)
    return tmp_path


def image(path, fmt):
    """Write a synthetic 8x8 image."""
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (8, 8), (200, 40, 40)).save(path, fmt)
    return path


def photo(path, fmt="JPEG"):
    """Write a synthetic 480x360 photo: a random 12x9 colour grid, smoothly upscaled."""
    path.parent.mkdir(parents=True, exist_ok=True)
    grid = Image.frombytes("RGB", (12, 9), random.Random(7).randbytes(12 * 9 * 3))
    grid.resize((480, 360), Image.Resampling.BICUBIC).save(path, fmt)
    return path


def screenshot(path, original):
    """Write a UI-like 1280x800 screenshot holding a 240x180 copy of the original."""
    canvas = Image.new("RGB", (1280, 800), (245, 245, 245))
    draw = ImageDraw.Draw(canvas)
    draw.rectangle((0, 0, 1280, 48), fill=(40, 44, 52))
    draw.rectangle((0, 48, 220, 800), fill=(225, 228, 232))
    for y in range(80, 760, 40):
        draw.rectangle((24, y, 196, y + 14), fill=(150, 155, 160))
        draw.rectangle((260, y, 1240 - (y * 7) % 400, y + 10), fill=(90, 90, 90))
    canvas.paste(Image.open(original).resize((240, 180)), (980, 80))
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(path, "PNG")
    return path


def text(path, content="# note\n"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


def notebook(path, cell):
    return text(
        path, json.dumps({"cells": [cell], "metadata": {}, "nbformat": 4, "nbformat_minor": 5})
    )


def showcase(repo):
    """Copy the three owner showcase files and their sidecars into the repository."""
    paths = []
    for name in SHOWCASE_FILES:
        for src in (SHOWCASE / name, (SHOWCASE / name).with_suffix(".md")):
            dst = repo / src.relative_to(ROOT)
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(src, dst)
            paths.append(dst)
    return paths


def git(repo, *args):
    """Run git in the repository; return the completed process."""
    return subprocess.run(
        ["git", "-C", str(repo), *args], check=False, capture_output=True, text=True
    )


def commit(repo, *paths, force=False, verify=True):
    """Stage the paths and commit; return the completed process."""
    add = ["git", "-C", str(repo), "add", *(["-f"] if force else []), "--"]
    subprocess.run(add + [str(p.relative_to(repo)) for p in paths], check=True)
    return git(repo, "commit", "-q", "-m", "test", *([] if verify else ["--no-verify"]))


def test_original_copied_to_docs_bin_fails(repo):
    original = image(repo / "data" / "raw" / "orig.jpg", "JPEG")
    copy = repo / "docs" / "x.bin"
    copy.parent.mkdir()
    shutil.copy(original, copy)
    result = commit(repo, copy)
    assert result.returncode == 1
    assert "docs/x.bin: byte-equal to the original data/raw/orig.jpg" in result.stderr


def test_original_copied_to_images_readme_with_sidecar_fails(repo):
    original = image(repo / "data" / "external" / "set" / "orig.webp", "WEBP")
    copy = repo / ".images_readme" / "x.webp"
    copy.parent.mkdir()
    shutil.copy(original, copy)
    result = commit(repo, copy, text(repo / ".images_readme" / "x.md"))
    assert result.returncode == 1
    assert "byte-equal to the original data/external/set/orig.webp" in result.stderr


def test_jpeg_renamed_notes_txt_fails(repo):
    jpeg = image(repo / "notes.txt", "JPEG")
    result = commit(repo, jpeg)
    assert result.returncode == 1
    assert "notes.txt: JPEG image outside .images_readme/" in result.stderr


def test_png_in_docs_fails(repo):
    result = commit(repo, image(repo / "docs" / "a.png", "PNG"))
    assert result.returncode == 1
    assert "docs/a.png: PNG image outside .images_readme/" in result.stderr


def test_data_jpeg_forced_fails(repo):
    result = commit(repo, image(repo / "data" / "x" / "a.jpg", "JPEG"), force=True)
    assert result.returncode == 1
    assert (
        "data/x/a.jpg: only .md and .gitkeep files may be committed under data/" in result.stderr
    )


def test_data_markdown_passes(repo):
    assert commit(repo, text(repo / "data" / "x" / "a.md")).returncode == 0


def test_images_readme_without_sidecar_fails(repo):
    result = commit(repo, image(repo / ".images_readme" / "d.webp", "WEBP"))
    assert result.returncode == 1
    assert "no sidecar .images_readme/d.md" in result.stderr


def test_images_readme_with_sidecar_passes(repo):
    webp = image(repo / ".images_readme" / "d.webp", "WEBP")
    assert commit(repo, webp, text(repo / ".images_readme" / "d.md")).returncode == 0


def test_notebook_with_attachment_fails(repo):
    cell = {
        "cell_type": "markdown",
        "metadata": {},
        "source": ["![a](attachment:a.png)"],
        "attachments": {"a.png": {"image/png": "iVBORw0KGgo="}},
    }
    result = commit(repo, notebook(repo / "nb.ipynb", cell))
    assert result.returncode == 1
    assert "nb.ipynb: notebook cell carries attachments" in result.stderr


def test_notebook_with_outputs_fails(repo):
    cell = {
        "cell_type": "code",
        "metadata": {},
        "source": ["1"],
        "execution_count": 1,
        "outputs": [
            {"output_type": "execute_result", "data": {"text/plain": "1"}, "metadata": {}}
        ],
    }
    result = commit(repo, notebook(repo / "nb.ipynb", cell))
    assert result.returncode == 1
    assert "notebooks with outputs are staged" in result.stderr


def test_clean_notebook_and_markdown_pass(repo):
    cell = {
        "cell_type": "code",
        "metadata": {},
        "source": ["1"],
        "execution_count": None,
        "outputs": [],
    }
    result = commit(repo, notebook(repo / "nb.ipynb", cell), text(repo / "README.md"))
    assert result.returncode == 0, result.stderr


def test_symlink_replaced_by_jpeg_fails(repo):
    link = repo / "docs" / "pic.jpg"
    link.parent.mkdir()
    link.symlink_to("target.txt")
    assert commit(repo, link).returncode == 0
    link.unlink()
    image(link, "JPEG")
    assert "T\tdocs/pic.jpg" in git(repo, "diff", "--name-status").stdout
    result = commit(repo, link)
    assert result.returncode == 1
    assert "docs/pic.jpg: JPEG image outside .images_readme/" in result.stderr


def test_lfs_pointer_fails(repo):
    pointer = "version https://git-lfs.github.com/spec/v1\noid sha256:" + "0" * 64 + "\nsize 9\n"
    result = commit(repo, text(repo / "docs" / "x.jpg", pointer))
    assert result.returncode == 1
    assert "docs/x.jpg: Git LFS pointer" in result.stderr


def test_gitattributes_filter_fails(repo):
    original = photo(repo / "data" / "raw" / "orig.jpg")
    copy = repo / "docs" / "x.jpg"
    copy.parent.mkdir()
    shutil.copy(original, copy)
    result = commit(repo, text(repo / ".gitattributes", "*.jpg filter=lfs\n"), copy)
    assert result.returncode == 1
    assert ".gitattributes: sets a filter= attribute" in result.stderr
    assert "docs/x.jpg: " in result.stderr  # an LFS pointer if git-lfs is installed, else a JPEG


def test_nbformat3_notebook_with_image_output_fails(repo):
    cell = {
        "cell_type": "code",
        "input": ["1"],
        "language": "python",
        "metadata": {},
        "outputs": [{"output_type": "display_data", "metadata": {}, "png": "iVBORw0KGgo="}],
    }
    nb = {"metadata": {}, "nbformat": 3, "nbformat_minor": 0, "worksheets": [{"cells": [cell]}]}
    result = commit(repo, text(repo / "nb.ipynb", json.dumps(nb)))
    assert result.returncode == 1
    assert "notebooks with outputs are staged:\n  nb.ipynb" in result.stderr


def test_svg_with_data_image_uri_fails(repo):
    uri = "data:" + "image/jpeg;base64,/9j/4AAQ"  # split, so this file holds no such URI
    svg = f'<svg xmlns="http://www.w3.org/2000/svg"><image href="{uri}"/></svg>\n'
    result = commit(repo, text(repo / "docs" / "pic.svg", svg))
    assert result.returncode == 1
    assert "docs/pic.svg: holds a data:image or data:video URI" in result.stderr


def test_zip_holding_jpeg_fails(repo):
    bundle = repo / "docs" / "bundle.zip"
    bundle.parent.mkdir()
    with zipfile.ZipFile(bundle, "w", zipfile.ZIP_STORED) as archive:
        archive.write(photo(repo / "data" / "raw" / "orig.jpg"), "orig.jpg")
    result = commit(repo, bundle)
    assert result.returncode == 1
    assert "docs/bundle.zip: zip archive" in result.stderr


def test_original_as_half_size_webp_in_images_readme_fails(repo):
    original = photo(repo / "data" / "raw" / "orig.jpg")
    copy = repo / ".images_readme" / "look.webp"
    copy.parent.mkdir()
    Image.open(original).resize((240, 180)).save(copy, "WEBP")
    result = commit(repo, copy, text(repo / ".images_readme" / "look.md"))
    assert result.returncode == 1
    assert ".images_readme/look.webp: near-copy of the original data/raw/orig.jpg" in result.stderr


def test_original_with_appended_byte_in_images_readme_fails(repo):
    original = photo(repo / "data" / "external" / "set" / "orig.jpg")
    copy = repo / ".images_readme" / "look.jpg"
    copy.parent.mkdir()
    copy.write_bytes(original.read_bytes() + b"\0")
    result = commit(repo, copy, text(repo / ".images_readme" / "look.md"))
    assert result.returncode == 1
    assert "look.jpg: near-copy of the original data/external/set/orig.jpg" in result.stderr
    assert "byte-equal" not in result.stderr


def test_git_mv_of_tracked_original_to_images_readme_fails(repo):
    original = photo(repo / "data" / "raw" / "orig.jpg")
    assert commit(repo, original, force=True, verify=False).returncode == 0
    sidecar = text(repo / ".images_readme" / "orig.md")
    assert git(repo, "mv", "data/raw/orig.jpg", ".images_readme/orig.jpg").returncode == 0
    result = commit(repo, sidecar)
    assert result.returncode == 1
    assert "orig.jpg: byte-equal to the original HEAD:data/raw/orig.jpg" in result.stderr
    assert "orig.jpg: near-copy of the original HEAD:data/raw/orig.jpg" in result.stderr


def test_screenshot_holding_small_original_passes(repo):
    original = photo(repo / "data" / "raw" / "orig.jpg")
    shot = screenshot(repo / ".images_readme" / "studio.png", original)
    result = commit(repo, shot, text(repo / ".images_readme" / "studio.md"))
    assert result.returncode == 0, result.stderr


def test_near_copy_check_without_venv_fails_closed(repo):
    (repo / ".venv").unlink()
    photo(repo / "data" / "raw" / "orig.jpg")
    drawing = image(repo / ".images_readme" / "d.webp", "WEBP")
    result = commit(repo, drawing, text(repo / ".images_readme" / "d.md"))
    assert result.returncode == 1
    assert "d.webp: the near-copy check needs Pillow in .venv/bin/python" in result.stderr


@pytest.fixture
def remote(repo, tmp_path_factory):
    """A bare repository registered as the origin of the repo."""
    bare = tmp_path_factory.mktemp("remote")
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)
    assert git(repo, "remote", "add", "origin", str(bare)).returncode == 0
    return bare


def test_no_verify_photo_commit_refused_at_push(repo, remote):
    assert commit(repo, image(repo / "docs" / "a.jpg", "JPEG"), verify=False).returncode == 0
    result = git(repo, "push", "-q", "origin", "HEAD:refs/heads/main")
    assert result.returncode != 0
    assert "pre-push: refused:" in result.stderr
    assert ":docs/a.jpg: JPEG image outside .images_readme/" in result.stderr
    assert git(remote, "for-each-ref").stdout == ""


def test_clean_push_passes(repo, remote):
    for name in ("README.md", "NOTES.md"):
        assert commit(repo, text(repo / name)).returncode == 0
        result = git(repo, "push", "-q", "origin", "HEAD:refs/heads/main")
        assert result.returncode == 0, result.stderr
    head = git(repo, "rev-parse", "HEAD").stdout
    assert git(remote, "rev-parse", "main").stdout == head


def test_showcase_passes_at_commit_and_push(repo, remote):
    result = commit(repo, *showcase(repo))
    assert result.returncode == 0, result.stderr
    result = git(repo, "push", "-q", "origin", "HEAD:refs/heads/main")
    assert result.returncode == 0, result.stderr


def test_fourth_image_under_showcase_fails(repo):
    extra = image(repo / "data" / "external" / "showcase" / "extra.png", "PNG")
    result = commit(repo, *showcase(repo), extra, text(extra.with_suffix(".md")), force=True)
    assert result.returncode == 1
    assert "data/external/showcase/extra.png: PNG image outside .images_readme/" in result.stderr
    assert "IMG_0020" not in result.stderr


def test_showcase_file_with_changed_byte_fails(repo):
    paths = showcase(repo)
    jpeg = repo / "data" / "external" / "showcase" / "IMG_0020.jpeg"
    b = bytearray(jpeg.read_bytes())
    b[len(b) // 2] ^= 1
    jpeg.write_bytes(b)
    result = commit(repo, *paths)
    assert result.returncode == 1
    assert "data/external/showcase/IMG_0020.jpeg: JPEG image outside .images_readme/" in (
        result.stderr
    )


def test_allow_line_outside_showcase_admits_nothing(repo):
    src = SHOWCASE / "IMG_0020.jpeg"
    moved = repo / "docs" / "IMG_0020.jpeg"
    moved.parent.mkdir()
    shutil.copy(src, moved)
    with open(repo / ".githooks" / "showcase.sha256", "a") as fh:
        fh.write(hashlib.sha256(src.read_bytes()).hexdigest() + "  docs/IMG_0020.jpeg\n")
    result = commit(repo, moved)
    assert result.returncode == 1
    assert "docs/IMG_0020.jpeg: JPEG image outside .images_readme/" in result.stderr


@pytest.mark.parametrize("dest", ["data/external/showcase/copy.mp4", ".images_readme/clip.mp4"])
def test_showcase_blob_at_another_path_fails(repo, dest):
    paths = showcase(repo)
    copy = repo / dest
    copy.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(SHOWCASE / "IMG_0020-clip-hd-5s.mp4", copy)
    result = commit(repo, *paths, copy, text(copy.with_suffix(".md")), force=True)
    assert result.returncode == 1
    assert dest + ": byte-equal to the original data/external/showcase/" in result.stderr


def test_original_copy_refused_beside_showcase(repo):
    original = photo(repo / "data" / "raw" / "orig.jpg")
    copy = repo / "docs" / "x.bin"
    copy.parent.mkdir()
    shutil.copy(original, copy)
    result = commit(repo, *showcase(repo), copy)
    assert result.returncode == 1
    assert "docs/x.bin: byte-equal to the original data/raw/orig.jpg" in result.stderr
    assert "IMG_0020" not in result.stderr


def test_second_commit_after_showcase_in_head_passes(repo, remote):
    assert commit(repo, *showcase(repo)).returncode == 0
    sidecar = repo / "data" / "external" / "showcase" / "IMG_0020.md"
    sidecar.write_text(sidecar.read_text() + "\n- note\n")
    result = commit(repo, sidecar, text(repo / "README.md"))
    assert result.returncode == 0, result.stderr
    result = git(repo, "push", "-q", "origin", "HEAD:refs/heads/main")
    assert result.returncode == 0, result.stderr
