"""Browser tests of the studio page: Chromium drives the page of a studio served with fakes.

Every studio runs in-process on an ephemeral loopback port over the synthetic image tree, with
FakeServer instead of ComfyUI and fake or real generators over it; no GPU, no real photo.
"""

import hashlib
from pathlib import Path
import re
from types import SimpleNamespace

from conftest import OUTPAINT, FakeGate, FakeGenerator, noise
from playwright.sync_api import Page, expect
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


def pick(page: Page, label: str) -> None:
    """Select a photo the way the user does."""
    page.get_by_label("Pick a photo").select_option(label=label)
    expect(page.locator("#preview-label")).to_have_text(label)


def newest_job(page: Page):
    """The first job row: the newest single job, or the frame row of the newest live photo."""
    return page.locator("#jobs .job").first


def wait_done(page: Page, timeout: float = 20_000) -> None:
    expect(newest_job(page).locator(".job-status")).to_have_text("done", timeout=timeout)


def real_generators() -> dict:
    return {"outpaint": Outpaint(FakeGate()), "video": Video()}


def tree_hashes(root: Path) -> dict[str, str]:
    return {
        str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(root.rglob("*"))
        if path.is_file() and not path.is_symlink()
    }


def test_page_shows_no_gpu_details(open_studio) -> None:
    studio = open_studio()
    page = studio.page
    expect(page.locator("#gpu-panel, #gpu-list, #gpu-error")).to_have_count(0)
    for text in ("NVIDIA", "GPU", "GB total", "GB free"):
        expect(page.locator("body")).not_to_contain_text(text)
    assert not any("gpu" in url.lower() for url in studio.requests), studio.requests
    pick(page, "raw/IMG_0001.jpg")
    page.get_by_role("button", name="Make Frame").click()
    wait_done(page)
    chips = newest_job(page).locator(".job-chips .chip")
    expect(chips).to_have_count(4)
    expect(newest_job(page).locator(".job-chips")).not_to_contain_text("GPU")


def test_over_large_job_shows_a_plain_local_compute_warning(open_studio) -> None:
    page = open_studio().page
    pick(page, "extended/4x3/IMG_0001.png")
    page.get_by_label("Clip resolution").select_option("2160")
    page.get_by_role("button", name="Make Clip").click()
    warning = page.locator("#vid-error")
    expect(warning).to_contain_text("needs 119.433 GB")
    expect(warning).to_contain_text("the workstation cannot provide it")
    for hidden in ("NVIDIA", "GPU", "GB free", "in total"):
        expect(warning).not_to_contain_text(hidden)


def test_picker_shows_names_and_one_preview(open_studio) -> None:
    studio = open_studio()
    page = studio.page
    expect(page.get_by_label("Pick a photo").locator("option")).to_have_text(LABELS)
    pick(page, "raw/IMG_0001.jpg")
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
    page.get_by_label("Upload a photo (JPEG, PNG or WebP)").set_input_files(photo)
    page.get_by_role("button", name="Upload", exact=True).click()
    expect(page.locator("#preview-label")).to_have_text("uploads/newphoto.png")
    expect(page.get_by_label("Pick a photo")).to_have_value("3/newphoto.png")
    assert (tmp_path / "state/uploads/newphoto.png").read_bytes() == photo.read_bytes()


def test_page_jobs_leave_the_input_tree_unchanged(
    open_studio, image_tree, fake_film, tmp_path
) -> None:
    before = tree_hashes(image_tree)
    studio = open_studio(real_generators())
    page = studio.page
    pick(page, "raw/IMG_0001.jpg")
    page.get_by_role("button", name="Make Frame").click()
    wait_done(page)
    page.get_by_role("button", name="Make Clip").click()
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
    pick(page, "raw/IMG_0001.jpg")
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


def test_use_as_clip_input_selects_the_frame(open_studio) -> None:
    studio = open_studio()
    page = studio.page
    pick(page, "raw/IMG_0001.jpg")
    expect(page.locator("#video-input")).to_have_text("IMG_0001.jpg")
    page.get_by_role("button", name="Make Frame").click()
    wait_done(page)
    frame = studio.client.get("/api/jobs")[1]["jobs"][0]
    result = frame["result"]
    expect(newest_job(page).get_by_role("link", name="Open Sidecar")).to_be_visible()
    newest_job(page).get_by_role("button", name="Use as Clip Input").click()
    expect(page.locator("#video-input")).to_have_text("Frame IMG_0001.png")  # C9: no folder
    expect(page.get_by_role("button", name="Use the Production Prompt")).to_be_visible()
    page.get_by_role("button", name="Make Clip").click()
    expect(page.locator("#jobs .job")).to_have_count(2)
    video = studio.client.get("/api/jobs")[1]["jobs"][0]
    assert (video["kind"], video["source"]) == ("video", result)
    titles = page.locator("#jobs .job-title")
    expect(titles).to_have_text(["Clip of frame IMG_0001.png", "Frame of IMG_0001.jpg"])
    for text in titles.all_inner_texts():  # no job folder path in a title
        assert "/" not in text and frame["id"] not in text and video["id"] not in text


def test_make_live_photo_queues_the_frame_and_its_video(open_studio) -> None:
    studio = open_studio()
    page = studio.page
    pick(page, "raw/IMG_0001.jpg")
    frame_preset, clip_preset = (
        page.get_by_label("Frame resolution"),
        page.get_by_label("Clip resolution"),
    )
    expect(frame_preset).to_have_value("1080")
    expect(frame_preset.locator("option:checked")).to_have_text("Full HD, 1080 lines")
    expect(clip_preset).to_have_value("720")
    expect(clip_preset.locator("option:checked")).to_have_text("HD, 720 lines")
    expect(frame_preset.locator("option")).to_have_text(
        ["HD, 720 lines", "Full HD, 1080 lines", "2K, 1440 lines", "UHD 4K, 2160 lines"]
    )
    page.get_by_label("Action", exact=True).fill("he smiles")
    page.get_by_role("button", name="Make Live Photo").click()
    expect(page.locator("#jobs .job")).to_have_count(2)
    expect(page.locator("#jobs .job .job-status")).to_have_text(["done", "done"])
    video, frame = studio.client.get("/api/jobs")[1]["jobs"]
    assert (frame["kind"], video["kind"], video["after"]) == ("outpaint", "video", frame["id"])
    assert video["source"] == frame["result"]
    assert (frame["params"]["size"], video["params"]["size"]) == ([1440, 1080], [960, 720])
    clip_row = page.locator("#jobs .job").nth(1)
    expect(clip_row.locator(".job-chips .chip")).to_have_text(
        ["10 s", "HD 960\u00d7720", "seed 42"]
    )
    assert (
        video["params"]["prompt"] == page.get_by_label(re.compile(r"^Final prompt")).input_value()
    )
    expect(clip_row.get_by_role("link", name="Open Clip")).to_be_visible()
    expect(newest_job(page).get_by_role("link", name="Open Frame")).to_be_visible()


@pytest.mark.parametrize(
    ("zone", "shown"), [("UTC", "27 Oct 2026, 22:30"), ("Asia/Tokyo", "28 Oct 2026, 07:30")]
)
def test_job_time_reads_as_local_day_month_year_and_time(open_studio, zone, shown) -> None:
    studio = open_studio(timezone_id=zone)
    client, page = studio.client, studio.page
    job = client.post("/api/jobs", OUTPAINT)[1]["job"]
    client.wait(job["id"], "done")
    studio.studio.jobs[job["id"]].created = "2026-10-27T23:30:00+01:00"
    page.reload()
    time = newest_job(page).locator("time")
    expect(time).to_have_text(shown)
    expect(time).to_have_attribute("datetime", "2026-10-27T23:30:00+01:00")
    card = page.locator("#jobs .job-card").first.inner_text()
    assert "2026-10-27T" not in card and "+01:00" not in card and "created" not in card


def test_live_photo_shows_the_frame_and_its_clip_in_one_card(open_studio) -> None:
    generator = FakeGenerator(block=True)
    studio = open_studio({"outpaint": generator, "video": generator})
    page = studio.page
    pick(page, "raw/IMG_0001.jpg")
    page.get_by_role("button", name="Make Live Photo").click()
    assert generator.started.wait(10)
    card = page.locator("#jobs .job-card")
    expect(card).to_have_count(1)
    expect(page.locator("#jobs .job")).to_have_count(2)
    expect(card.locator(".job-title")).to_have_text("Live photo of IMG_0001.jpg")
    expect(card.locator(".card-status")).to_have_text("running: frame")
    frame_row, clip_row = page.locator("#jobs .job").first, page.locator("#jobs .job").nth(1)
    expect(frame_row.locator(".job-step")).to_have_text(re.compile(r"^Step 1 of 2: Frame"))
    expect(clip_row.locator(".job-step")).to_have_text(re.compile(r"^Step 2 of 2: Clip"))
    expect(clip_row.locator(".job-status")).to_have_text("queued")  # P5
    expect(clip_row.locator(".job-stage")).to_have_text("Queued")
    expect(clip_row.locator(".job-percent")).to_have_text("0 %")
    expect(clip_row.get_by_role("button", name="Cancel")).to_be_visible()
    placeholder = clip_row.locator(".job-media .placeholder")
    expect(placeholder).to_have_css("aspect-ratio", "960 / 720")
    generator.release.set()
    expect(card.locator(".card-status")).to_have_text("done")
    expect(page.locator("#jobs .job .job-status")).to_have_text(["done", "done"])
    expect(card.locator(".job-progress")).to_have_count(2)
    for bar in card.locator(".job-progress").all():
        expect(bar).to_be_hidden()
    expect(frame_row.locator(".job-media img")).to_have_css("aspect-ratio", "1440 / 1080")
    expect(clip_row.locator(".job-media > *")).to_have_css("aspect-ratio", "960 / 720")
    title = card.locator(".job-title").inner_text()
    assert "/" not in title and "jobs" not in title


def test_cancelled_frame_shows_its_live_photo_cancelled(open_studio) -> None:
    generator = FakeGenerator(block=True)
    studio = open_studio({"outpaint": generator, "video": generator})
    page = studio.page
    pick(page, "images/IMG_0003.png")
    page.get_by_role("button", name="Make Frame").click()  # keeps the worker busy
    assert generator.started.wait(10)
    pick(page, "raw/IMG_0001.jpg")
    page.get_by_role("button", name="Make Live Photo").click()
    expect(page.locator("#jobs .job-card")).to_have_count(2)
    live = page.locator("#jobs .job-card").first
    live.locator(".job").first.get_by_role("button", name="Cancel").click()
    generator.release.set()
    expect(live.locator(".job .job-status")).to_have_text(["cancelled", "failed"])
    expect(live.locator(".card-status")).to_have_text("cancelled")  # P3
    expect(live.locator(".job").nth(1).locator(".error")).to_contain_text("was cancelled")


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
    page.get_by_role("button", name="Make Clip").click()
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
    page.get_by_label("Frame resolution").select_option("1440")
    page.get_by_role("button", name="Make Frame").click()
    expect(page.locator("#jobs .job")).to_have_count(1)

    video = {"Action": "he waves", "Camera": "slow push in", "Hold": "hands on the table"}
    video |= {"Soundscape": "quiet room", "Music": "soft piano"}
    for label, value in video.items():
        page.get_by_label(label, exact=True).fill(value)
    final = page.get_by_label(re.compile(r"^Final prompt"))
    expect(final).to_have_value(h3_prompt(*video.values()))
    final.fill("an edited final prompt")
    page.get_by_label("Duration").select_option("6")
    page.get_by_label("Clip resolution").select_option("1080")
    page.get_by_label("Seed").fill("7")
    page.get_by_role("button", name="Make Clip").click()
    expect(page.locator("#jobs .job")).to_have_count(2)

    page.reload()
    pick(page, "raw/WIDE_0002.jpg")  # another image keeps the preset
    expect(page.get_by_label("Prompt", exact=True)).to_have_value(OUTPAINT_PROMPT)
    expect(page.get_by_label("Action", exact=True)).to_have_value("")
    pick(page, "raw/IMG_0001.jpg")
    for label, value in {**outpaint, **video}.items():
        expect(page.get_by_label(label, exact=True)).to_have_value(value)
    expect(page.get_by_label("Aspect ratio")).to_have_value("16x9")
    expect(page.get_by_label("Frame resolution")).to_have_value("1440")
    expect(final).to_have_value("an edited final prompt")
    expect(page.get_by_label("Duration")).to_have_value("6")
    expect(page.get_by_label("Clip resolution")).to_have_value("1080")
    expect(page.get_by_label("Seed")).to_have_value("7")


def test_job_progress_bar_advances(open_studio) -> None:
    generator = FakeGenerator(block=True)
    studio = open_studio({"outpaint": generator, "video": generator})
    page = studio.page
    pick(page, "raw/IMG_0001.jpg")
    page.get_by_role("button", name="Make Frame").click()
    assert generator.started.wait(10)
    job = newest_job(page)
    status, stage, bar = (
        job.locator(".job-status"),
        job.locator(".job-stage"),
        job.locator(".job-progress"),
    )
    expect(stage).to_have_text("Loading model")
    expect(status).to_have_text("running: loading model")
    expect(job.locator(".job-media .placeholder")).to_be_visible()
    server = studio.studio.server
    steps = [
        ({"type": "executing", "data": {"node": "10"}}, "Sampling", 10),
        (
            {"type": "progress", "data": {"node": "10", "value": 3, "max": 20}},
            "Sampling, step 3 of 20",
            21.7,
        ),
        ({"type": "executing", "data": {"node": "12"}}, "Decoding", 90),
    ]
    for event, text, percent in steps:
        server.on_event(event)
        expect(stage).to_have_text(text, timeout=REFRESH_MS)
        expect(status).to_have_text(f"running: {text.split(',')[0].lower()}")
        expect(bar).to_have_attribute("aria-valuenow", str(percent))
        expect(job.locator(".job-percent")).to_have_text(f"{round(percent)} %")
    expect(job.get_by_role("button", name="Cancel")).to_be_visible()
    generator.release.set()
    expect(status).to_have_text("done", timeout=REFRESH_MS + 1000)
    expect(bar).to_be_hidden()  # a done job shows no stage line and no progress bar
    expect(stage).to_be_hidden()
    expect(job.get_by_role("button", name="Cancel")).to_be_hidden()
    expect(job.locator(".job-media img")).to_be_visible()
    panel = page.locator("#jobs-panel")
    expect(panel).not_to_contain_text("Stage:")
    expect(panel.locator("progress")).to_have_count(0)


def test_cancel_and_failure_show_on_the_job(open_studio) -> None:
    running = FakeGenerator(block=True)
    studio = open_studio({"outpaint": running, "video": running})
    page = studio.page
    pick(page, "raw/IMG_0001.jpg")
    page.get_by_role("button", name="Make Frame").click()
    assert running.started.wait(10)
    page.get_by_role("button", name="Make Clip").click()
    expect(page.locator("#jobs .job")).to_have_count(2)
    queued = newest_job(page)
    expect(queued.locator(".job-status")).to_have_text("queued")
    expect(queued.locator(".job-stage")).to_have_text("Queued")
    queued.get_by_role("button", name="Cancel").click()
    expect(queued.locator(".job-status")).to_have_text("cancelled")
    expect(queued.locator(".job-media")).to_be_hidden()
    running.release.set()
    expect(page.locator("#jobs .job").nth(1).locator(".job-status")).to_have_text("done")

    def fail(job, server, folder):
        raise RuntimeError("the fake generator failed")

    studio.studio.generators["video"] = SimpleNamespace(run=fail)
    page.get_by_role("button", name="Make Clip").click()
    failed = newest_job(page)
    expect(failed.locator(".job-status")).to_have_text("failed")
    expect(failed.locator(".error")).to_have_text("the fake generator failed")
    expect(failed.locator(".error")).to_be_visible()
    expect(failed.locator(".job-progress")).to_be_hidden()
    expect(failed.locator(".job-media")).to_be_hidden()
    expect(failed.locator(".job-actions a, .job-actions button")).to_have_count(0)


def test_crop_step_shows_on_the_job(open_studio) -> None:
    page = open_studio(real_generators()).page
    pick(page, "raw/WIDE_0002.jpg")  # 16:9 at the default 4:3: cropped
    page.get_by_role("button", name="Make Frame").click()
    wait_done(page)
    expect(newest_job(page).locator(".job-chips .chip")).to_have_text(
        ["4:3", "Full HD 1440\u00d71080", "cropped", "cfg 1.0"]
    )


def test_page_requests_only_the_studio(open_studio) -> None:
    studio = open_studio()
    pick(studio.page, "raw/IMG_0001.jpg")
    studio.page.get_by_role("button", name="Make Frame").click()
    wait_done(studio.page)
    assert studio.requests
    assert all(url.startswith(studio.client.url + "/") for url in studio.requests), studio.requests
    assert studio.client.url.startswith("http://127.0.0.1:")


@pytest.mark.parametrize("viewport", [(1440, 900), (390, 844)])
def test_layout_fits_the_width_and_labels_every_control(open_studio, viewport) -> None:
    studio = open_studio(viewport=viewport)
    page = studio.page
    pick(page, "raw/IMG_0001.jpg")
    page.get_by_role("button", name="Make Live Photo").click()
    expect(page.locator("#jobs .job-status")).to_have_text(["done", "done"])
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
    unlabelled = page.evaluate(
        """[...document.querySelectorAll('input, select, textarea')]
            .filter((el) => !el.labels.length && !el.getAttribute('aria-label'))
            .map((el) => el.outerHTML)"""
    )
    assert unlabelled == []
    beside = page.evaluate(
        """document.querySelector('#jobs-panel').getBoundingClientRect().left >
           document.querySelector('.controls').getBoundingClientRect().right"""
    )
    assert beside == (viewport[0] >= 1200)  # L4 two columns from 1200 px, L7 one below
    columns = page.evaluate(
        "getComputedStyle(document.querySelector('#jobs .job-body')).gridTemplateColumns"
    )
    assert len(columns.split()) == (2 if viewport[0] >= 1200 else 1)  # K4 at 1440 and 390
