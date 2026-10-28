"use strict";
// Every URL is relative, so the page works at / and under the JupyterHub proxy/<port>/.

const H3_FIELDS = ["action", "camera", "hold", "soundscape", "music"];
const DEFAULT_FIELDS = { action: "", camera: "Static Shot", hold: "", soundscape: "", music: "N/A" };
const state = { image: null, video: null, preset: null };
const cards = new Map(); // job card of each job, or of each live photo, by key
let assembly = 0;

const $ = (id) => document.getElementById(id);
const fileUrl = (ref) => `api/file?ref=${encodeURIComponent(ref)}`;
const fileName = (label) => label.split("/").pop();

function el(tag, className = "", text = "") {
  const node = document.createElement(tag);
  node.className = className;
  node.textContent = text;
  return node;
}

async function api(path, options = {}) {
  const response = await fetch(path, options);
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.error || `${response.status} ${response.statusText}`);
  return body;
}

function post(path, body) {
  return api(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

function show(id, error) {
  $(id).textContent = error ? error.message : "";
}

function choose(id, value, fallback) {
  $(id).value = String(value);
  if ($(id).selectedIndex < 0) $(id).value = String(fallback); // a value of an earlier version
}

// --- image -----------------------------------------------------------------------------------

async function loadImages(selectRef) {
  try {
    const { images } = await api("api/images");
    $("image-select").replaceChildren(...images.map(({ ref, label }) => new Option(label, ref)));
    $("picker").hidden = !images.length;
    $("image-empty").hidden = images.length > 0;
    $("image-select").value = selectRef || (state.image && state.image.ref) || "";
    if (selectRef) await pickImage();
  } catch (error) {
    show("image-error", error);
  }
}

async function pickImage() {
  const option = $("image-select").selectedOptions[0];
  if (!option) return;
  state.image = { ref: option.value, label: option.text };
  $("preview").src = fileUrl(state.image.ref);
  $("preview-label").textContent = state.image.label;
  $("preview-figure").hidden = false;
  await Promise.all([loadOutpaintPrompts(), setVideoInput(state.image)]);
}

async function upload() {
  const file = $("upload-file").files[0];
  if (!file) return show("image-error", new Error("Choose a file to upload first."));
  try {
    const { ref } = await api(`api/uploads?name=${encodeURIComponent(file.name)}`, {
      method: "POST",
      headers: { "Content-Type": file.type || "application/octet-stream" },
      body: file,
    });
    $("upload-file").value = "";
    show("image-error");
    await loadImages(ref);
  } catch (error) {
    show("image-error", error);
  }
}

// --- outpaint --------------------------------------------------------------------------------

function cfgText(cfg) {
  return Number.isInteger(cfg) ? cfg.toFixed(1) : String(cfg);
}

function cfgNote() {
  const silent = $("out-negative").value.trim() && Number($("out-cfg").value) === 1;
  $("cfg-note").textContent = silent ? "The negative prompt has no effect at cfg 1.0." : "";
}

async function loadOutpaintPrompts() {
  const ref = state.image.ref;
  try {
    const { saved, preset } = await api(`api/prompts?ref=${encodeURIComponent(ref)}&kind=outpaint`);
    if (state.image.ref !== ref) return; // another image was picked meanwhile
    const fields = { aspect: "4x3", resolution: 1080, ...preset, ...saved };
    $("out-aspect").value = fields.aspect;
    choose("out-resolution", fields.resolution, 1080);
    $("out-prompt").value = fields.prompt;
    $("out-negative").value = fields.negative_prompt;
    $("out-cfg").value = cfgText(fields.cfg);
    cfgNote();
    show("out-error");
  } catch (error) {
    show("out-error", error);
  }
}

// --- video -----------------------------------------------------------------------------------

async function assemble() {
  const id = ++assembly;
  const fields = Object.fromEntries(H3_FIELDS.map((name) => [name, $(`vid-${name}`).value]));
  try {
    const { prompt } = await post("api/h3-prompt", fields);
    if (id === assembly) $("vid-prompt").value = prompt; // only the newest assembly lands
  } catch (error) {
    show("vid-error", error);
  }
}

async function setVideoInput(item) {
  state.video = item;
  const name = fileName(item.label);
  $("video-input").textContent = item.label.startsWith("jobs/") ? `Frame ${name}` : name;
  try {
    const { saved, preset } = await api(
      `api/prompts?ref=${encodeURIComponent(item.ref)}&kind=video`,
    );
    if (state.video.ref !== item.ref) return;
    state.preset = preset && preset.prompt;
    $("vid-preset").hidden = !state.preset;
    const fields = { ...DEFAULT_FIELDS, ...(saved && saved.fields) };
    for (const name of H3_FIELDS) $(`vid-${name}`).value = fields[name];
    $("vid-duration").value = String((saved && saved.duration) || 10);
    choose("vid-resolution", (saved && saved.resolution) || 720, 720);
    $("vid-seed").value = saved ? saved.seed : 42;
    show("vid-error");
    if (saved) $("vid-prompt").value = saved.prompt;
    else await assemble();
  } catch (error) {
    show("vid-error", error);
  }
}

// --- jobs ------------------------------------------------------------------------------------

const MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
const PRESET_NAMES = { 720: "HD", 1080: "Full HD", 1440: "2K", 2160: "UHD 4K" };
const ACTIVE = ["queued", "running"];

async function submitJob(errorId, body) {
  try {
    await post("api/jobs", body);
    show(errorId);
    await loadJobs();
    // two columns: the window stays put and the Jobs panel shows its top; one column: scroll to it
    if (matchMedia("(min-width: 1200px)").matches) $("jobs-panel").scrollTop = 0;
    else $("jobs-panel").scrollIntoView({ block: "start" });
  } catch (error) {
    show(errorId, error);
  }
}

// "27 Oct 2026, 22:30" in the browser's local time
function when(iso) {
  const date = new Date(iso);
  const pad = (number) => String(number).padStart(2, "0");
  const day = `${date.getDate()} ${MONTHS[date.getMonth()]} ${date.getFullYear()}`;
  return `${day}, ${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

// the kind words and the file name of a job's title; a frame input is jobs/<id>/<file>
function titleParts(job) {
  const label = job.source.label;
  if (job.kind === "outpaint") return ["Frame of ", fileName(label)];
  if (!label.startsWith("jobs/")) return ["Clip of ", fileName(label)];
  if (label.split("/").length === 3) return ["Clip of frame ", fileName(label)];
  return ["Clip of a removed frame", ""];
}

function sizeText(p) {
  if (!p.size) return p.resolution ? String(p.resolution) : `${p.width} px wide`; // earlier versions
  const name = PRESET_NAMES[p.resolution];
  return `${name ? `${name} ` : ""}${p.size.join("×")}`;
}

function chipTexts(job) {
  const p = job.params;
  if (job.kind === "outpaint") {
    const frame = p.frame || "outpainted sideways";
    return [p.aspect.replace("x", ":"), sizeText(p), frame, `cfg ${cfgText(p.cfg)}`];
  }
  return [`${p.duration} s`, sizeText(p), `seed ${p.seed}`];
}

function setStatus(chip, state, text) {
  chip.className = `${chip.classList[0]} chip status ${state}`;
  chip.textContent = text;
}

function cardHead([kind, name], created, chip) {
  const head = el("div", "job-head");
  const heading = el("div", "job-heading");
  const title = el("h3", "job-title");
  const time = el("time", "", when(created));
  title.append(el("span", "job-kind", kind), el("span", "job-name", name));
  time.dateTime = created;
  heading.append(title, time);
  head.append(heading, chip);
  return head;
}

// one job: a card head of its own, or a step line inside a live photo card
function jobRow(job, step) {
  const row = el("div", "job");
  const body = el("div", "job-body");
  const details = el("div", "job-details");
  const status = el("span", "job-status");
  const chips = el("div", "job-chips");
  const run = el("div", "job-run");
  const line = el("div", "job-run-line");
  const bar = el("div", "job-progress");
  row.dataset.jobId = job.id;
  if (step) {
    const stepLine = el("div", "job-step");
    stepLine.append(el("span", "", step), status);
    details.append(stepLine);
  } else {
    row.append(cardHead(titleParts(job), job.created, status));
  }
  chips.append(...chipTexts(job).map((text) => el("span", "chip", text)));
  line.append(el("span", "job-stage"), el("span", "job-percent"));
  bar.setAttribute("role", "progressbar");
  bar.setAttribute("aria-label", `Progress of the ${job.kind === "outpaint" ? "frame" : "clip"}`);
  bar.setAttribute("aria-valuemin", "0");
  bar.setAttribute("aria-valuemax", "100");
  bar.append(el("i"));
  run.append(line, bar);
  details.append(chips, el("p", "error"), run, el("div", "job-actions"));
  body.append(el("div", "job-media"), details);
  row.append(body);
  return row;
}

function updateRow(row, job) {
  const active = ACTIVE.includes(job.state);
  setStatus(
    row.querySelector(".job-status"),
    job.state,
    job.state === "running" ? `running: ${job.stage}` : job.state,
  );
  if (job.error) row.querySelector(".error").textContent = job.error;
  row.querySelector(".job-run").hidden = !active;
  if (active) {
    const step = job.stage === "sampling" && job.steps ? `, step ${job.step} of ${job.steps}` : "";
    const stage = `${job.stage}${step}`;
    const bar = row.querySelector(".job-progress");
    row.querySelector(".job-stage").textContent = stage[0].toUpperCase() + stage.slice(1);
    row.querySelector(".job-percent").textContent = `${Math.round(job.percent)} %`;
    bar.setAttribute("aria-valuenow", String(job.percent));
    bar.classList.toggle("running", job.state === "running");
    bar.firstChild.style.width = `${job.percent}%`;
  }
  updateMedia(row, job);
  updateActions(row, job);
}

// the result when done, a placeholder of the same size while queued or running, else nothing
function updateMedia(row, job) {
  const media = row.querySelector(".job-media");
  const done = job.state === "done" && job.result;
  const shows = done ? job.result.ref : ACTIVE.includes(job.state) ? "placeholder" : "";
  if (media.dataset.shows === shows) return;
  media.dataset.shows = shows;
  media.hidden = !shows;
  row.querySelector(".job-body").classList.toggle("with-media", Boolean(shows));
  if (!shows) return media.replaceChildren();
  const video = done && job.result.label.toLowerCase().endsWith(".mp4");
  const node = el(done ? (video ? "video" : "img") : "div", done ? "" : "placeholder");
  if (done) node.src = fileUrl(job.result.ref);
  if (video) Object.assign(node, { controls: true, preload: "metadata" });
  else if (done) node.alt = `Frame of ${fileName(job.source.label)}`;
  if (job.params.size) node.style.aspectRatio = job.params.size.join(" / ");
  media.replaceChildren(node);
}

function updateActions(row, job) {
  const done = job.state === "done" && job.result;
  const kind = done ? "done" : ACTIVE.includes(job.state) ? "active" : "";
  const box = row.querySelector(".job-actions");
  if (box.dataset.kind === kind) return;
  box.dataset.kind = kind;
  box.replaceChildren();
  if (kind === "active") {
    const cancel = el("button", "list danger cancel", "Cancel");
    cancel.type = "button";
    cancel.addEventListener("click", async () => {
      try {
        await post(`api/jobs/${job.id}/cancel`, {});
        await loadJobs();
      } catch (error) {
        row.querySelector(".error").textContent = error.message;
      }
    });
    box.append(cancel);
  } else if (kind === "done") {
    const frame = job.kind === "outpaint";
    for (const [text, ref] of [
      [frame ? "Open Frame" : "Open Clip", job.result.ref],
      ["Open Sidecar", job.sidecar.ref],
    ]) {
      box.append(Object.assign(el("a", "btn list", text), {
        href: fileUrl(ref),
        target: "_blank",
        rel: "noopener",
      }));
    }
    if (frame) {
      const use = el("button", "list animate", "Use as Clip Input");
      use.type = "button";
      use.addEventListener("click", () => {
        setVideoInput(job.result);
        $("vid-action").focus();
      });
      box.append(use);
    }
  }
}

function singleCard(job) {
  const li = el("li", "job-card");
  li.append(jobRow(job));
  return li;
}

function liveCard(frame, clip) {
  const li = el("li", "job-card live");
  const head = cardHead(
    ["Live photo of ", fileName(frame.source.label)],
    frame.created,
    el("span", "card-status"),
  );
  li.append(head, jobRow(frame, "Step 1 of 2: Frame"), jobRow(clip, "Step 2 of 2: Clip"));
  return li;
}

// the first job that is not done sets the card state, frame first; a cancelled frame fails its clip
function updateLive(li, frame, clip) {
  const [frameRow, clipRow] = li.querySelectorAll(".job");
  updateRow(frameRow, frame);
  updateRow(clipRow, clip);
  const first = frame.state === "done" ? clip : frame;
  const text =
    first.state === "running" ? `running: ${first === frame ? "frame" : "clip"}` : first.state;
  setStatus(li.querySelector(".card-status"), first.state, text);
}

async function loadJobs() {
  let jobs;
  try {
    ({ jobs } = await api("api/jobs"));
  } catch {
    $("jobs-error").textContent =
      "The studio server did not answer. The page asks again every second.";
    return;
  }
  $("jobs-error").textContent = "";
  const byId = new Map(jobs.map((job) => [job.id, job]));
  const paired = new Set(jobs.filter((job) => byId.has(job.after)).map((job) => job.after));
  const keys = [];
  for (const job of jobs) {
    if (paired.has(job.id)) continue; // a frame shows in the card of its clip
    const frame = byId.get(job.after);
    const key = `${frame ? "live" : "job"}:${job.id}`;
    if (!cards.has(key)) cards.set(key, frame ? liveCard(frame, job) : singleCard(job));
    if (frame) updateLive(cards.get(key), frame, job);
    else updateRow(cards.get(key).firstChild, job);
    keys.push(key);
  }
  for (const [key, li] of cards) {
    if (!keys.includes(key)) {
      li.remove(); // a newer job of the same source and kind replaced it
      cards.delete(key);
    }
  }
  const list = $("jobs");
  keys.forEach((key, position) => {
    const li = cards.get(key);
    if (list.children[position] !== li) list.insertBefore(li, list.children[position] || null);
  });
  $("jobs-empty").textContent =
    "No jobs yet. Pick a photo, then press Make Live Photo, Make Frame or Make Clip.";
  $("jobs-empty").hidden = jobs.length > 0;
}

async function poll() {
  await loadJobs();
  setTimeout(poll, 1000);
}

// --- wiring ----------------------------------------------------------------------------------

$("image-select").addEventListener("change", pickImage);
$("upload-button").addEventListener("click", upload);
$("out-negative").addEventListener("input", cfgNote);
$("out-cfg").addEventListener("input", cfgNote);
for (const name of H3_FIELDS) $(`vid-${name}`).addEventListener("input", assemble);
$("vid-preset").addEventListener("click", () => {
  $("vid-prompt").value = state.preset;
});

function outpaintBody() {
  return {
    kind: "outpaint",
    ref: state.image.ref,
    aspect: $("out-aspect").value,
    resolution: Number($("out-resolution").value),
    prompt: $("out-prompt").value,
    negative_prompt: $("out-negative").value,
    cfg: Number($("out-cfg").value),
  };
}

function videoSettings() {
  return {
    prompt: $("vid-prompt").value,
    duration: Number($("vid-duration").value),
    resolution: Number($("vid-resolution").value),
    seed: Number($("vid-seed").value),
    fields: Object.fromEntries(H3_FIELDS.map((name) => [name, $(`vid-${name}`).value])),
  };
}

$("out-generate").addEventListener("click", () => {
  if (!state.image) return show("out-error", new Error("Select a photo first."));
  submitJob("out-error", outpaintBody());
});

// the frame job, then a video of its result with the Video panel's settings
$("out-pipeline").addEventListener("click", () => {
  if (!state.image) return show("out-error", new Error("Select a photo first."));
  submitJob("out-error", { ...outpaintBody(), video: videoSettings() });
});

$("vid-generate").addEventListener("click", () => {
  if (!state.video) return show("vid-error", new Error("Select a photo first."));
  submitJob("vid-error", { kind: "video", ref: state.video.ref, ...videoSettings() });
});

function setTheme(theme) {
  document.documentElement.dataset.theme = theme;
  for (const button of document.querySelectorAll(".theme-switch button")) {
    button.setAttribute("aria-pressed", String(button.value === theme));
  }
}

for (const button of document.querySelectorAll(".theme-switch button")) {
  button.addEventListener("click", () => {
    setTheme(button.value);
    try {
      localStorage.setItem("studio-theme", button.value);
    } catch {
      // storage blocked: the choice lasts for this page only
    }
  });
}

setTheme(document.documentElement.dataset.theme);
for (const name of H3_FIELDS) $(`vid-${name}`).value = DEFAULT_FIELDS[name];
assemble();
loadImages();
poll();
