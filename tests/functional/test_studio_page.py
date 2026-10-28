"""Browser tests of the studio page: Chromium drives the page of a studio served with fakes.

Every studio runs in-process on an ephemeral loopback port over the synthetic image tree, with
FakeServer instead of ComfyUI and fake or real generators over it; no GPU, no real photo.
"""

import hashlib
from pathlib import Path
import re
from types import SimpleNamespace

from conftest import FakeGate, FakeGenerator, noise
from playwright.sync_api import Page, expect, sync_playwright
import pytest

from henryk_media.studio.generators import Outpaint, Video
from henryk_media.studio.prompts import OUTPAINT_NEGATIVE, OUTPAINT_PROMPT, h3_prompt

LABELS = [
    "extended/4x3/IMG_0001.png",
    "images/IMG_0003.png",
    "raw/IMG_0001.jpg",
    "raw/WIDE_0002.jpg",
]
REFRESH_MS = 2000  # PROGRESS: the page refreshes a running job at least every 2 s


@pytest.fixture(scope="module")
def browser():
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        yield browser
        browser.close()


@pytest.fixture
def open_studio(browser, make_studio, serve):
    """Serve a studio with the given generators and open its page; returns studio, client, page."""
    contexts = []

    def open_(generators: dict | None = None, viewport=(1280, 900)) -> SimpleNamespace:
        studio = make_studio(generators)
        client = serve(studio)
        context = browser.new_context(viewport={"width": viewport[0], "height": viewport[1]})
        contexts.append(context)
        page = context.new_page()
        requests: list[str] = []
        page.on("request", lambda request: requests.append(request.url))
        page.goto(client.url + "/")
        expect(page.get_by_label(re.compile(r"^GPU 0:"))).to_be_visible()
        return SimpleNamespace(studio=studio, client=client, page=page, requests=requests)

    yield open_
    for context in contexts:
        context.close()


def pick(page: Page, label: str, gpu: int | None = 1) -> None:
    """Select a GPU and an image the way the user does."""
    if gpu is not None:
        with page.expect_response("**/api/gpu"):
            page.get_by_label(re.compile(rf"^GPU {gpu}:")).check()
    page.get_by_label("Pick an image").select_option(label=label)
    expect(page.locator("#preview-label")).to_have_text(label)


def newest_job(page: Page):
    return page.locator("#jobs .job").first


def wait_done(page: Page, timeout: float = 20_000) -> None:
    expect(newest_job(page).locator(".job-stage")).to_have_text("Stage: done", timeout=timeout)


def real_generators() -> dict:
    return {"outpaint": Outpaint(FakeGate()), "video": Video()}


def tree_hashes(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file() and not path.is_symlink()
    }


def test_gpu_picker_lists_every_gpu(open_studio) -> None:
    studio = open_studio()
    radios = studio.page.get_by_role("radio")
    expect(radios).to_have_count(3)
    expect(studio.page.locator("#gpu-list")).to_contain_text(
        "GPU 0: NVIDIA RTX PRO 4000 Blackwell, 25.7 GB total, 25.2 GB free"
    )
    for index in (1, 2):
        expect(studio.page.get_by_label(re.compile(rf"^GPU {index}: NVIDIA"))).to_be_visible()
    with studio.page.expect_response("**/api/gpu"):
        studio.page.get_by_label(re.compile(r"^GPU 2:")).check()
    studio.page.reload()
    expect(studio.page.get_by_label(re.compile(r"^GPU 2:"))).to_be_checked()
    assert studio.studio.selected.index == 2


def test_picker_shows_names_and_one_preview(open_studio) -> None:
    studio = open_studio()
    page = studio.page
    expect(page.get_by_label("Pick an image").locator("option")).to_have_text(LABELS)
    pick(page, "raw/IMG_0001.jpg", gpu=None)
    preview = page.locator("img")
    expect(preview).to_have_count(1)
    expect(preview).to_have_attribute("src", "api/file?ref=0%2FIMG_0001.jpg")
    page.wait_for_function("document.querySelector('#preview').naturalWidth === 600")
    files = [url for url in studio.requests if "/api/file?" in url]
    assert files == [studio.client.url + "/api/file?ref=0%2FIMG_0001.jpg"]  # no other image


def test_uploaded_image_appears_in_the_picker(open_studio, tmp_path) -> None:
    studio = open_studio()
    page = studio.page
    photo = tmp_path / "new photo.png"
    noise((40, 30)).save(photo)
    page.get_by_label("Upload an image (JPEG, PNG or WebP)").set_input_files(photo)
    page.get_by_role("button", name="Upload", exact=True).click()
    expect(page.locator("#preview-label")).to_have_text("uploads/newphoto.png")
    expect(page.get_by_label("Pick an image")).to_have_value("3/newphoto.png")
    assert (tmp_path / "state/uploads/newphoto.png").read_bytes() == photo.read_bytes()


def test_page_jobs_leave_the_input_tree_unchanged(
    open_studio, image_tree, fake_film, tmp_path
) -> None:
    before = tree_hashes(image_tree)
    studio = open_studio(real_generators())
    page = studio.page
    pick(page, "raw/IMG_0001.jpg")
    page.get_by_role("button", name="Generate outpaint").click()
    wait_done(page)
    page.get_by_role("button", name="Generate video").click()
    expect(page.locator("#jobs .job")).to_have_count(2)
    wait_done(page)
    assert tree_hashes(image_tree) == before
    jobs = studio.client.get("/api/jobs")[1]["jobs"]
    assert [(job["kind"], job["state"]) for job in jobs] == [
        ("video", "done"),
        ("outpaint", "done"),
    ]
    for job in jobs:
        name = job["result"]["label"].split("/")[-1]
        assert (tmp_path / "state/jobs" / job["id"] / name).is_file()


def test_negative_prompt_note_follows_cfg(open_studio) -> None:
    page = open_studio().page
    pick(page, "raw/IMG_0001.jpg", gpu=None)
    expect(page.get_by_label("Prompt", exact=True)).to_have_value(OUTPAINT_PROMPT)
    expect(page.get_by_label("Negative prompt")).to_have_value(OUTPAINT_NEGATIVE)
    expect(page.get_by_label("cfg")).to_have_value("1.0")
    note = page.locator("#cfg-note")
    page.get_by_label("Negative prompt").fill("")
    expect(note).to_be_hidden()
    page.get_by_label("Negative prompt").fill("person")
    expect(note).to_have_text("The negative prompt has no effect at cfg 1.0.")
    expect(note).to_be_visible()
    page.get_by_label("cfg").fill("2.0")
    expect(note).to_be_hidden()


def test_animate_this_selects_the_outpaint_result(open_studio) -> None:
    studio = open_studio()
    page = studio.page
    pick(page, "raw/IMG_0001.jpg")
    page.get_by_role("button", name="Generate outpaint").click()
    wait_done(page)
    result = studio.client.get("/api/jobs")[1]["jobs"][0]["result"]
    expect(newest_job(page).get_by_role("link", name="Open the sidecar")).to_be_visible()
    newest_job(page).get_by_role("button", name="Animate this").click()
    expect(page.locator("#video-input")).to_have_text(result["label"])
    expect(page.get_by_role("button", name="Use the production prompt")).to_be_visible()
    page.get_by_role("button", name="Generate video").click()
    expect(page.locator("#jobs .job")).to_have_count(2)
    video = studio.client.get("/api/jobs")[1]["jobs"][0]
    assert (video["kind"], video["source"]) == ("video", result)


def test_edited_final_prompt_is_submitted(open_studio, fake_server, fake_film) -> None:
    studio = open_studio(real_generators())
    page = studio.page
    pick(page, "raw/IMG_0001.jpg")
    page.get_by_label("Action", exact=True).fill("the boy at the table smiles")
    final = page.get_by_label(re.compile(r"^Final prompt"))
    assembled = h3_prompt("the boy at the table smiles", "Static Shot", "", "", "N/A")
    expect(final).to_have_value(assembled)
    edited = assembled.replace("smiles", "smiles and nods once") + "\n"
    final.fill(edited)
    page.get_by_role("button", name="Generate video").click()
    wait_done(page)
    assert fake_server.instances[0].graphs[-1]["6"]["inputs"]["prompt"] == edited


def test_prompts_restore_when_the_image_is_selected_again(open_studio) -> None:
    studio = open_studio()
    page = studio.page
    pick(page, "raw/IMG_0001.jpg")
    expect(page.get_by_label("Prompt", exact=True)).to_have_value(OUTPAINT_PROMPT)
    outpaint = {"Prompt": "an edited room", "Negative prompt": "an edited negative", "cfg": "2.5"}
    for label, value in outpaint.items():
        page.get_by_label(label, exact=True).fill(value)
    page.get_by_label("Aspect ratio").select_option("16x9")
    page.get_by_label("Width", exact=True).select_option("1536")
    page.get_by_role("button", name="Generate outpaint").click()
    expect(page.locator("#jobs .job")).to_have_count(1)

    video = {"Action": "he waves", "Camera": "slow push in", "Hold": "hands on the table"}
    video |= {"Soundscape": "quiet room", "Music": "soft piano"}
    for label, value in video.items():
        page.get_by_label(label, exact=True).fill(value)
    final = page.get_by_label(re.compile(r"^Final prompt"))
    expect(final).to_have_value(h3_prompt(*video.values()))
    final.fill("an edited final prompt")
    page.get_by_label("Duration").select_option("6")
    page.get_by_label("Resolution").select_option("480x320")
    page.get_by_label("Seed").fill("7")
    page.get_by_role("button", name="Generate video").click()
    expect(page.locator("#jobs .job")).to_have_count(2)

    page.reload()
    pick(page, "raw/WIDE_0002.jpg", gpu=None)  # another image keeps the preset
    expect(page.get_by_label("Prompt", exact=True)).to_have_value(OUTPAINT_PROMPT)
    expect(page.get_by_label("Action", exact=True)).to_have_value("")
    pick(page, "raw/IMG_0001.jpg", gpu=None)
    for label, value in {**outpaint, **video}.items():
        expect(page.get_by_label(label, exact=True)).to_have_value(value)
    expect(page.get_by_label("Aspect ratio")).to_have_value("16x9")
    expect(page.get_by_label("Width", exact=True)).to_have_value("1536")
    expect(final).to_have_value("an edited final prompt")
    expect(page.get_by_label("Duration")).to_have_value("6")
    expect(page.get_by_label("Resolution")).to_have_value("480x320")
    expect(page.get_by_label("Seed")).to_have_value("7")


def test_job_progress_bar_advances(open_studio) -> None:
    generator = FakeGenerator(block=True)
    studio = open_studio({"outpaint": generator, "video": generator})
    page = studio.page
    pick(page, "raw/IMG_0001.jpg")
    page.get_by_role("button", name="Generate outpaint").click()
    assert generator.started.wait(10)
    job = newest_job(page)
    stage, bar = job.locator(".job-stage"), job.locator("progress")
    expect(stage).to_have_text("Stage: loading model")
    server = studio.studio.server
    steps = [
        ({"type": "executing", "data": {"node": "10"}}, "Stage: sampling", 10),
        (
            {"type": "progress", "data": {"node": "10", "value": 3, "max": 20}},
            "Stage: sampling, step 3 of 20",
            21.7,
        ),
        ({"type": "executing", "data": {"node": "12"}}, "Stage: decoding", 90),
    ]
    for event, text, percent in steps:
        server.on_event(event)
        expect(stage).to_have_text(text, timeout=REFRESH_MS)
        expect(bar).to_have_js_property("value", percent)
        expect(job.locator(".job-percent")).to_have_text(f"{round(percent)} %")
    expect(job.get_by_role("button", name="Cancel")).to_be_visible()
    generator.release.set()
    expect(stage).to_have_text("Stage: done", timeout=REFRESH_MS + 1000)
    expect(bar).to_have_js_property("value", 100)
    expect(job.get_by_role("button", name="Cancel")).to_be_hidden()


def test_cancel_and_failure_show_on_the_job(open_studio) -> None:
    running = FakeGenerator(block=True)
    studio = open_studio({"outpaint": running, "video": running})
    page = studio.page
    pick(page, "raw/IMG_0001.jpg", gpu=None)
    page.get_by_role("button", name="Generate outpaint").click()
    expect(page.locator("#out-error")).to_have_text("select a GPU first")
    with page.expect_response("**/api/gpu"):
        page.get_by_label(re.compile(r"^GPU 1:")).check()
    page.get_by_role("button", name="Generate outpaint").click()
    assert running.started.wait(10)
    page.get_by_role("button", name="Generate video").click()
    expect(page.locator("#jobs .job")).to_have_count(2)
    queued = newest_job(page)
    expect(queued.locator(".job-stage")).to_have_text("Stage: queued")
    queued.get_by_role("button", name="Cancel").click()
    expect(queued.locator(".job-stage")).to_have_text("Stage: cancelled")
    running.release.set()
    expect(page.locator("#jobs .job").nth(1).locator(".job-stage")).to_have_text("Stage: done")

    def fail(job, server, folder):
        raise RuntimeError("the fake generator failed")

    studio.studio.generators["video"] = SimpleNamespace(run=fail)
    page.get_by_role("button", name="Generate video").click()
    failed = newest_job(page)
    expect(failed.locator(".job-stage")).to_have_text("Stage: failed")
    expect(failed.locator(".error")).to_have_text("the fake generator failed")


def test_page_requests_only_the_studio(open_studio) -> None:
    studio = open_studio()
    pick(studio.page, "raw/IMG_0001.jpg")
    studio.page.get_by_role("button", name="Generate outpaint").click()
    wait_done(studio.page)
    assert studio.requests
    assert all(url.startswith(studio.client.url + "/") for url in studio.requests), studio.requests
    assert studio.client.url.startswith("http://127.0.0.1:")


@pytest.mark.parametrize("viewport", [(1280, 900), (375, 740)])
def test_layout_fits_the_width_and_labels_every_control(open_studio, viewport) -> None:
    page = open_studio(viewport=viewport).page
    pick(page, "extended/4x3/IMG_0001.png")
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    unlabelled = page.evaluate(
        """[...document.querySelectorAll('input, select, textarea')]
            .filter((el) => !el.labels.length && !el.getAttribute('aria-label'))
            .map((el) => el.outerHTML)"""
    )
    assert unlabelled == []
    side_by_side = page.evaluate(
        """document.querySelector('#outpaint-panel').getBoundingClientRect().top ===
           document.querySelector('#video-panel').getBoundingClientRect().top"""
    )
    assert side_by_side == (viewport[0] >= 960)
