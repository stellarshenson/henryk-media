"use strict";
// Every URL is relative, so the page works at / and under the JupyterHub proxy/<port>/.

const H3_FIELDS = ["action", "camera", "hold", "soundscape", "music"];
const DEFAULT_FIELDS = { action: "", camera: "Static Shot", hold: "", soundscape: "", music: "N/A" };
const state = { gpu: null, image: null, video: null, preset: null };
const jobItems = new Map();
let assembly = 0;

const $ = (id) => document.getElementById(id);
const fileUrl = (ref) => `api/file?ref=${encodeURIComponent(ref)}`;

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

// --- GPU -------------------------------------------------------------------------------------

async function loadGpus() {
  try {
    const { gpus, selected } = await api("api/gpus");
    state.gpu = selected;
    $("gpu-list").replaceChildren(
      ...gpus.map((gpu) => {
        const label = document.createElement("label");
        const input = document.createElement("input");
        label.className = "gpu";
        input.type = "radio";
        input.name = "gpu";
        input.value = gpu.index;
        input.checked = gpu.index === selected;
        input.addEventListener("change", () => selectGpu(gpu.index));
        label.append(
          input,
          `GPU ${gpu.index}: ${gpu.name}, ${gpu.total_gb} GB total, ${gpu.free_gb} GB free`,
        );
        return label;
      }),
    );
    show("gpu-error");
  } catch (error) {
    show("gpu-error", error);
  }
}

async function selectGpu(index) {
  try {
    state.gpu = (await post("api/gpu", { index })).selected;
    show("gpu-error");
  } catch (error) {
    show("gpu-error", error);
    for (const input of document.querySelectorAll('input[name="gpu"]')) {
      input.checked = Number(input.value) === state.gpu; // back to the studio's selection
    }
  }
}

// --- image -----------------------------------------------------------------------------------

async function loadImages(selectRef) {
  try {
    const { images } = await api("api/images");
    $("image-select").replaceChildren(...images.map(({ ref, label }) => new Option(label, ref)));
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
    const fields = { aspect: "4x3", width: 1280, ...preset, ...saved };
    $("out-aspect").value = fields.aspect;
    $("out-width").value = String(fields.width);
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
  $("video-input").textContent = item.label;
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
    $("vid-resolution").value = (saved && saved.resolution) || "1024x768";
    $("vid-seed").value = saved ? saved.seed : 42;
    show("vid-error");
    if (saved) $("vid-prompt").value = saved.prompt;
    else await assemble();
  } catch (error) {
    show("vid-error", error);
  }
}

// --- jobs ------------------------------------------------------------------------------------

async function submitJob(errorId, body) {
  try {
    await post("api/jobs", body);
    show(errorId);
    await loadJobs();
    $("jobs-panel").scrollIntoView({ block: "start" });
  } catch (error) {
    show(errorId, error);
  }
}

function describe(job) {
  const p = job.params;
  const settings =
    job.kind === "outpaint"
      ? `${p.aspect.replace("x", ":")} at ${p.width} px, cfg ${cfgText(p.cfg)}`
      : `${p.duration} s, ${p.resolution}, seed ${p.seed}`;
  const kind = job.kind === "outpaint" ? "Outpaint" : "Video";
  return `${kind} of ${job.source.label}: ${settings}, GPU ${job.gpu.index}, created ${job.created}`;
}

function jobItem(job) {
  const li = document.createElement("li");
  li.className = "job";
  li.dataset.jobId = job.id;
  li.innerHTML = `
    <div class="job-title"></div>
    <div><progress max="100" value="0"></progress> <span class="job-percent"></span></div>
    <div class="job-stage"></div>
    <p class="error"></p>
    <div class="result"></div>
    <div class="links"></div>
    <button type="button" class="cancel">Cancel</button>
    <button type="button" class="animate" hidden>Animate this</button>`;
  li.querySelector(".job-title").textContent = describe(job);
  li.querySelector("progress").setAttribute("aria-label", `Progress of job ${job.id}`);
  li.querySelector(".cancel").addEventListener("click", async () => {
    try {
      await post(`api/jobs/${job.id}/cancel`, {});
      await loadJobs();
    } catch (error) {
      li.querySelector(".error").textContent = error.message;
    }
  });
  li.querySelector(".animate").addEventListener("click", () => {
    setVideoInput(li.result);
    $("vid-action").focus();
  });
  return li;
}

function updateItem(li, job) {
  const step = job.stage === "sampling" && job.steps ? `, step ${job.step} of ${job.steps}` : "";
  li.querySelector(".job-stage").textContent = `Stage: ${job.stage}${step}`;
  li.querySelector("progress").value = job.percent;
  li.querySelector(".job-percent").textContent = `${Math.round(job.percent)} %`;
  if (job.error) li.querySelector(".error").textContent = job.error;
  li.querySelector(".cancel").hidden = !["queued", "running"].includes(job.state);
  if (job.result && !li.result) {
    li.result = job.result;
    const video = job.result.label.toLowerCase().endsWith(".mp4");
    const media = document.createElement(video ? "video" : "img");
    media.src = fileUrl(job.result.ref);
    if (video) media.controls = true;
    else media.alt = `Result of job ${job.id}`;
    li.querySelector(".result").append(media);
    const links = [
      ["Open the result", job.result.ref],
      ["Open the sidecar", job.sidecar.ref],
    ].map(([text, ref]) => Object.assign(document.createElement("a"), {
      textContent: text,
      href: fileUrl(ref),
      target: "_blank",
    }));
    li.querySelector(".links").append(...links);
    li.querySelector(".animate").hidden = job.kind !== "outpaint";
  }
}

async function loadJobs() {
  let jobs;
  try {
    ({ jobs } = await api("api/jobs"));
  } catch {
    return; // the next poll asks again
  }
  const list = $("jobs");
  const ids = new Set(jobs.map((job) => job.id));
  for (const [id, li] of jobItems) {
    if (!ids.has(id)) {
      li.remove(); // a newer job of the same source and kind replaced it
      jobItems.delete(id);
    }
  }
  jobs.forEach((job, position) => {
    if (!jobItems.has(job.id)) jobItems.set(job.id, jobItem(job));
    const li = jobItems.get(job.id);
    if (list.children[position] !== li) list.insertBefore(li, list.children[position] || null);
    updateItem(li, job);
  });
  $("jobs-empty").hidden = jobs.length > 0;
}

async function poll() {
  await loadJobs();
  setTimeout(poll, 1000);
}

// --- wiring ----------------------------------------------------------------------------------

$("gpu-refresh").addEventListener("click", loadGpus);
$("image-select").addEventListener("change", pickImage);
$("upload-button").addEventListener("click", upload);
$("out-negative").addEventListener("input", cfgNote);
$("out-cfg").addEventListener("input", cfgNote);
for (const name of H3_FIELDS) $(`vid-${name}`).addEventListener("input", assemble);
$("vid-preset").addEventListener("click", () => {
  $("vid-prompt").value = state.preset;
});

$("out-generate").addEventListener("click", () => {
  if (!state.image) return show("out-error", new Error("Select an image first."));
  submitJob("out-error", {
    kind: "outpaint",
    ref: state.image.ref,
    aspect: $("out-aspect").value,
    width: Number($("out-width").value),
    prompt: $("out-prompt").value,
    negative_prompt: $("out-negative").value,
    cfg: Number($("out-cfg").value),
  });
});

$("vid-generate").addEventListener("click", () => {
  if (!state.video) return show("vid-error", new Error("Select an image first."));
  submitJob("vid-error", {
    kind: "video",
    ref: state.video.ref,
    prompt: $("vid-prompt").value,
    duration: Number($("vid-duration").value),
    resolution: $("vid-resolution").value,
    seed: Number($("vid-seed").value),
    fields: Object.fromEntries(H3_FIELDS.map((name) => [name, $(`vid-${name}`).value])),
  });
});

for (const name of H3_FIELDS) $(`vid-${name}`).value = DEFAULT_FIELDS[name];
assemble();
loadGpus();
loadImages();
poll();
