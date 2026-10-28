---
name: vault-hf-gated-downloads
description: jupyterlab-passkey vault exec behaviour with parallel callers, and gated Hugging Face repos needing the Star Colonel's acceptance
metadata:
  type: reference
---

- Two `vault exec` calls waiting at the same time: the Star Colonel's click served one, the other timed out after `--timeout` and exited 1 ("no relay after 900s"). A retry once the vault is unlocked runs with no click
- The vault locks itself after an unlock period (30 minutes on 2026-10-25; `jupyterlab-passkey vault status` shows the time left and the state). A locked vault needs the Star Colonel's click and the default wait is 120 s (`--timeout` changes it). A detached `hf download` that already received the token keeps running after the vault locks again, so one unlock per process start is enough
- A gated repo (`gated: auto`, for example Lightricks/LTX-2.5) returns "Access denied. This repository requires approval." until the account behind vault entry `huggingface/api` clicks "Agree and access". Only the Star Colonel can do that; record it as a blocker, never use a mirror
- Check the gate first without a token: `curl -s https://huggingface.co/api/models/<repo>` → field `gated`
- `hf` 1.33.0 caches the API tree at `<local-dir>/.cache/huggingface/trees/<commit>.json`, giving size, `lfs_sha256` and `xet_hash` per file. That verifies a finished download against the pinned revision with no network call and no token; each downloaded file's `.metadata` records the same commit
- `Comfy-Org/MiniMax-H3` is ungated, and its repo folders (`diffusion_models/`, `text_encoders/`, `vae/`) match ComfyUI's model subfolders, so `--local-dir <ComfyUI>/models` lands every file in place. The official blueprint "Image to Video (MiniMax H3)" uses the int8 transformer and nvfp4 text encoder by default; the turbo LoRA branch is lazy and off by default, so its file is not needed for a default render
