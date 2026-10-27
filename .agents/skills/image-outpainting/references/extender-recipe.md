# Extender recipe

FLUX 3 Klein with the ausboss outpaint LoRA renders both side panels at full 1280-wide frame size on one pinned GPU; every value below is recorded in the tile's sidecar and checkpoint.

## Model

- `black-forest-labs/flux-3-image-klein`: `flux3-image-klein-bf16.safetensors`, 5.6B bf16 distilled
- VAE `flux2-ae.safetensors`
- Text encoder `qwen3vl_4b_bf16.safetensors` with shards merged; `CLIPLoader` type `flux3`
- LoRA `ausboss/FLUX-3-Image-Klein-Outpaint-LoRA`: `flux-3-image-klein-outpaint.safetensors`, strength 1.5 through `LoraLoaderModelOnly`
- Registry entry `flux3-klein` in `src/henryk_media/imaging/registry.py`, graph `graphs/flux3_klein.json`
- Licence FLUX Kommunity v1.0, non-commercial private use

## Settings

- steps 16, cfg 1.0, euler, simple, denoise 1.0, render scale 1.0
- Render scale starts at 1.0 (`FALLBACK_SCALES` in `src/henryk_media/imaging/extender.py` is 1.0, 0.71, 0.5)
- Seed 42 upward, six attempts 42-47 (`SEEDS` 6); the first passing frame is kept, otherwise the last frame is kept and marked failed
- Out of memory: retry at 0.71 then 0.5 render scale, largest fitting size kept

## Prompt

The positive prompt is below; its opening sentence is the LoRA trigger. The negative prompt is `person, child, man, woman, crowd, face, hands, portrait, new person, extra person, second child, mirrored child, reflected child, reflection of a person, different face, changed expression, deformed, distorted, blurry, low quality, text, watermark`; `{{NEGATIVE_PROMPT}}` is inert at cfg 1.0.

```
Outpaint the image: replace the solid grey areas with an empty continuation of the same room and scene beyond the frame, keeping the existing picture unchanged. Continue the same floor, the same wall and background and the same soft indoor daylight as the photo, at the same perspective, scale and brightness. The added area holds no person, no child, no face, no hands and no figure; keep every person already in the photo exactly as they are, with the same faces, expressions, hair and clothes.
```

## Server

- GPU `GPU-a44e514a-aa5b-2844-35f1-4be28e1921e5`, nvidia-smi index 1
- Pin `CUDA_DEVICE_ORDER=PCI_BUS_ID` and `CUDA_VISIBLE_DEVICES` to that UUID before torch import
- `Setup.load("tmp/workflows/image-extender/setup-extender.json")`, then `ComfyServer(setup)`; port 8189
- `ComfyServer` refuses a port that already answers
- Server log `logs/image-extender-server.log`, written with `2>&1` and `< /dev/null`
- Exact start command:

```
cd /home/lab/workspace/private/henryk/henryk-media/models/photo-animation/ComfyUI && CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=GPU-a44e514a-aa5b-2844-35f1-4be28e1921e5 HF_HUB_OFFLINE=1 YOLO_OFFLINE=1 MPLBACKEND=Agg setsid nohup .venv/bin/python main.py --listen 127.0.0.1 --port 8189 --disable-auto-launch --offline --disable-product-tips --feature-flag enable_telemetry=false --input-directory /home/lab/workspace/private/henryk/henryk-media/models/photo-animation/ComfyUI-extender-io/input --output-directory /home/lab/workspace/private/henryk/henryk-media/models/photo-animation/ComfyUI-extender-io/output --temp-directory /home/lab/workspace/private/henryk/henryk-media/models/photo-animation/ComfyUI-extender-io/temp --user-directory /home/lab/workspace/private/henryk/henryk-media/models/photo-animation/ComfyUI-extender-io/user --previews-directory /home/lab/workspace/private/henryk/henryk-media/models/photo-animation/ComfyUI-extender-io/previews > /home/lab/workspace/private/henryk/henryk-media/logs/image-extender-server.log 2>&1 < /dev/null &
```
