# photo-animation

Third-party code and weights that animate still photos. The folder `models/photo-animation/` is gitignored; the commands below recreate it.

## LivePortrait

- `LivePortrait/` - clone of https://github.com/KwaiVGI/LivePortrait at commit `9b294b3d0536135442ea73cb01e6cb3ca7029dd3` (2026-06-02)
- `LivePortrait/pretrained_weights/` - Hugging Face `KlingTeam/LivePortrait` at revision `82a4fa6735ca58432b6ce39301b4b9ee066dea47`, 2.0 GB, humans and animals models plus the InsightFace detector
- `LivePortrait/ffmpeg/ffmpeg` - symlink to the ffmpeg 4.2.2 binary inside the `imageio-ffmpeg` package in `.venv`. `inference.py` adds `<current directory>/ffmpeg` to PATH, so run it from inside `LivePortrait/`. There is no ffprobe, so LivePortrait does not copy audio from a driving video
- The Python environment is the project `.venv` (dependencies in `pyproject.toml`), not LivePortrait's own requirements files

## Licences

- LivePortrait code: MIT
- InsightFace detector models (`pretrained_weights/insightface/`): non-commercial research use only. The Star Colonel accepted this for private family use on 2026-10-24

## Recreate

Run from the project root. The vault command raises a JupyterLab notification that must be clicked.

```bash
git clone https://github.com/KwaiVGI/LivePortrait models/photo-animation/LivePortrait
git -C models/photo-animation/LivePortrait checkout 9b294b3d0536135442ea73cb01e6cb3ca7029dd3
(cd models/photo-animation/LivePortrait && jupyterlab-passkey vault exec --caller henryk-media --timeout 900 \
  --env HF_TOKEN=huggingface/api -- hf download KlingTeam/LivePortrait \
  --revision 82a4fa6735ca58432b6ce39301b4b9ee066dea47 --local-dir pretrained_weights \
  --exclude "*.git*" --exclude "README.md" --exclude "docs/*")
make create_environment requirements register_environment
mkdir -p models/photo-animation/LivePortrait/ffmpeg
ln -sfn "$(.venv/bin/python -c 'import imageio_ffmpeg; print(imageio_ffmpeg.get_ffmpeg_exe())')" \
  models/photo-animation/LivePortrait/ffmpeg/ffmpeg
```

Check with LivePortrait's bundled example on GPU index 1 (RTX PRO 6000):

```bash
cd models/photo-animation/LivePortrait
CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=GPU-a44e514a-aa5b-2844-35f1-4be28e1921e5 \
  ../../../.venv/bin/python inference.py -s assets/examples/source/s0.jpg \
  -d assets/examples/driving/d0.mp4 -o ../../../tmp/liveportrait-check/
```

## ComfyUI with AdvancedLivePortrait

LivePortrait runs inside ComfyUI with a node pack that makes idle motion from edited expressions, with no driving clip.

- `ComfyUI/` - clone of https://github.com/comfyanonymous/ComfyUI at commit `7cebca52227c63b4180ceed448cbd7ad22903b6d` (2026-10-23, ComfyUI 0.42.0)
- `ComfyUI/custom_nodes/ComfyUI-AdvancedLivePortrait/` - clone of https://github.com/PowerHouseMan/ComfyUI-AdvancedLivePortrait at commit `3bba732915e22f18af0d221b9c5c282990181f1b` (2024-08-21)
- `ComfyUI/custom_nodes/ComfyUI-VideoHelperSuite/` - clone of https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite at commit `4d907bee61e92c2e65af3bd6383a4e4d356126d1` (2026-09-01)
- `ComfyUI/models/liveportrait/` - five safetensors from Hugging Face `Kijai/LivePortrait_safetensors` at revision `59f30f36d7b791929c25437df7461d5b0e0010b1`, 0.52 GB
- `ComfyUI/models/ultralytics/face_yolov8n.pt` - from Hugging Face `Bingsu/adetailer` at revision `53cc19de382014514d9d4038601d261a7faa9b7b`, 6.2 MB
- `ComfyUI/.venv/` - own environment from `make comfyui_environment`: Python 3.13, torch 2.14.1+cu130, ultralytics 8.4.187, ultralytics usage events off (`yolo settings sync=False`, stored in `~/.config/Ultralytics/settings.json`)
- The node pack downloads a weight file only when it is missing, so with the files above it makes no download call
- VideoHelperSuite writes a PNG of the first frame next to every mp4 in `ComfyUI/output/`. The ExpressionEditor node writes preview PNGs to `ComfyUI/temp/`

### Licences

- ComfyUI and ComfyUI-VideoHelperSuite: GPL-3.0
- ComfyUI-AdvancedLivePortrait: no licence file. Its `pyproject.toml` names a `LICENSE` file that the repository does not contain, so the code carries no licence grant
- `Kijai/LivePortrait_safetensors`: converted from `KlingTeam/LivePortrait` weights (MIT); the Hugging Face repository has no licence field
- `face_yolov8n.pt` (`Bingsu/adetailer`): Apache-2.0
- ultralytics: AGPL-3.0, which permits private use

### Recreate

Run from the project root. The vault command raises a JupyterLab notification that must be clicked.

```bash
git clone https://github.com/comfyanonymous/ComfyUI models/photo-animation/ComfyUI
git -C models/photo-animation/ComfyUI checkout 7cebca52227c63b4180ceed448cbd7ad22903b6d
git clone https://github.com/PowerHouseMan/ComfyUI-AdvancedLivePortrait \
  models/photo-animation/ComfyUI/custom_nodes/ComfyUI-AdvancedLivePortrait
git -C models/photo-animation/ComfyUI/custom_nodes/ComfyUI-AdvancedLivePortrait checkout 3bba732915e22f18af0d221b9c5c282990181f1b
git clone https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite \
  models/photo-animation/ComfyUI/custom_nodes/ComfyUI-VideoHelperSuite
git -C models/photo-animation/ComfyUI/custom_nodes/ComfyUI-VideoHelperSuite checkout 4d907bee61e92c2e65af3bd6383a4e4d356126d1
make comfyui_environment
(cd models/photo-animation/ComfyUI && jupyterlab-passkey vault exec --caller henryk-media --timeout 900 \
  --env HF_TOKEN=huggingface/api -- hf download Kijai/LivePortrait_safetensors \
  --revision 59f30f36d7b791929c25437df7461d5b0e0010b1 --local-dir models/liveportrait \
  appearance_feature_extractor.safetensors motion_extractor.safetensors warping_module.safetensors \
  spade_generator.safetensors stitching_retargeting_module.safetensors)
(cd models/photo-animation/ComfyUI && jupyterlab-passkey vault exec --caller henryk-media --timeout 900 \
  --env HF_TOKEN=huggingface/api -- hf download Bingsu/adetailer face_yolov8n.pt \
  --revision 53cc19de382014514d9d4038601d261a7faa9b7b --local-dir models/ultralytics)
```

### Start and stop the server

The server listens on 127.0.0.1 only and runs on GPU index 2 (RTX PRO 5000). `--offline` turns off the paid API nodes and blocks the web frontend from the internet; the telemetry feature flag is off by default and is set off explicitly. ComfyUI-Manager is not installed, and ComfyUI itself has no update check. `HF_HUB_OFFLINE=1` stops Hugging Face calls and `YOLO_OFFLINE=1` stops the ultralytics online and update checks.

```bash
cd models/photo-animation/ComfyUI
CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=GPU-1223ff00-ce71-874f-592e-a4429e9f47ba \
  HF_HUB_OFFLINE=1 YOLO_OFFLINE=1 setsid nohup .venv/bin/python main.py --listen 127.0.0.1 --port 8188 \
  --disable-auto-launch --offline --disable-product-tips --feature-flag enable_telemetry=false \
  > ../../../logs/comfyui-server.log 2>&1 &
kill "$(pgrep -f '^\.venv/bin/python main.py --listen 127.0.0.1 --port 8188')"
```

The API graph template with fill-in markers is `tmp/workflows/advanced-liveportrait-build/workflow-api.json`; `smoke_test.py` beside it fills and submits it.

## Wan2.2-I2V-A14B (no notebook; Wan2.2 rejected 2026-10-25)

Image-to-video model that redraws the whole photo and animates it from a text prompt. It runs in the ComfyUI checkout above with core nodes only.

- Model: Wan2.2-I2V-A14B by Wan-AI (Alibaba, 2025-07), two 14B experts - a high-noise expert runs the early denoising steps, a low-noise expert the late steps
- Weights: the Comfy-Org repackaged files at fp16, 68,776,044,287 B (68.78 GB) in total. The SHA-256 of every file matched the Hugging Face API on 2026-10-24
- Licence: Apache-2.0 for `Wan-AI/Wan2.2-I2V-A14B`, `Comfy-Org/Wan-2.2` and `Comfy-Org/Wan-2.1`; none of them is gated
- `Comfy-Org/Wan_2.2_ComfyUI_Repackaged` and `Comfy-Org/Wan_2.1_ComfyUI_repackaged`, the names in the ComfyUI template notes, now resolve to `Comfy-Org/Wan-2.2` and `Comfy-Org/Wan-2.1`

| File in `ComfyUI/models/` | Repository, revision | Size (bytes) |
|---|---|---|
| `diffusion_models/wan2.2_i2v_high_noise_14B_fp16.safetensors` | `Comfy-Org/Wan-2.2`, `ee6f4a40737a995bf5818954cfce6d59443b0f04` | 28,577,914,792 |
| `diffusion_models/wan2.2_i2v_low_noise_14B_fp16.safetensors` | `Comfy-Org/Wan-2.2`, `ee6f4a40737a995bf5818954cfce6d59443b0f04` | 28,577,914,792 |
| `text_encoders/umt5_xxl_fp16.safetensors` | `Comfy-Org/Wan-2.1`, `123acf1cc74bccbb9bfff8ac1ee72edc08c2341d` | 11,366,399,385 |
| `vae/wan_2.1_vae.safetensors` | `Comfy-Org/Wan-2.2`, `ee6f4a40737a995bf5818954cfce6d59443b0f04` | 253,815,318 |

### Recreate

Run from the project root after the ComfyUI recreate steps above. The repository paths start with `split_files/`, so the files download to a staging folder and move into the ComfyUI subfolders. The vault command raises a JupyterLab notification that must be clicked.

```bash
STAGE=models/photo-animation/.download-wan22
MODELS=models/photo-animation/ComfyUI/models
jupyterlab-passkey vault exec --caller henryk-media --timeout 900 --env HF_TOKEN=huggingface/api -- bash -c "
  hf download Comfy-Org/Wan-2.2 --revision ee6f4a40737a995bf5818954cfce6d59443b0f04 --local-dir $STAGE \
    split_files/diffusion_models/wan2.2_i2v_high_noise_14B_fp16.safetensors \
    split_files/diffusion_models/wan2.2_i2v_low_noise_14B_fp16.safetensors \
    split_files/vae/wan_2.1_vae.safetensors &&
  hf download Comfy-Org/Wan-2.1 --revision 123acf1cc74bccbb9bfff8ac1ee72edc08c2341d --local-dir $STAGE \
    split_files/text_encoders/umt5_xxl_fp16.safetensors"
mv $STAGE/split_files/diffusion_models/wan2.2_i2v_*_fp16.safetensors $MODELS/diffusion_models/
mv $STAGE/split_files/text_encoders/umt5_xxl_fp16.safetensors $MODELS/text_encoders/
mv $STAGE/split_files/vae/wan_2.1_vae.safetensors $MODELS/vae/
trash-put $STAGE
```

### Start and stop the server

This server has its own port (8191) and its own input, output, temp, user and previews directories under `models/photo-animation/ComfyUI-i2v-io/wan22/`, so nothing it reads or writes lands in the shared ComfyUI folders. It runs on GPU index 2 (RTX PRO 5000) with the same quiet flags as the AdvancedLivePortrait server. ComfyUI writes temp files to `temp/temp/`, and the user directory also holds this server's `comfyui.db`.

```bash
IO=$PWD/models/photo-animation/ComfyUI-i2v-io/wan22
mkdir -p $IO/{input,output,temp,user,previews}
cd models/photo-animation/ComfyUI
CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=GPU-1223ff00-ce71-874f-592e-a4429e9f47ba \
  HF_HUB_OFFLINE=1 YOLO_OFFLINE=1 setsid nohup .venv/bin/python main.py --listen 127.0.0.1 --port 8191 \
  --disable-auto-launch --offline --disable-product-tips --feature-flag enable_telemetry=false \
  --input-directory $IO/input --output-directory $IO/output --temp-directory $IO/temp \
  --user-directory $IO/user --previews-directory $IO/previews \
  > ../../../logs/image-to-video-server-wan22.log 2>&1 &
kill "$(pgrep -f '^\.venv/bin/python main.py --listen 127.0.0.1 --port 8191')"
```

The API graph template with fill-in markers is `tmp/workflows/image-to-video/workflow-api-wan22.json`, built from the official ComfyUI template `video_wan2_2_14B_i2v.json` with fp16 files, the native sampler settings (UniPC, 40 steps, experts split at step 15, CFG 3.5, shift 5.0) and 16 fps. `smoke_test_wan22.py` beside it fills and submits it.
