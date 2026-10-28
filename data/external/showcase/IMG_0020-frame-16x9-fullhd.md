# IMG_0020-frame-16x9-fullhd.png - studio job 20261028-145745-dc5f64, a generated image, not a photograph

A byte copy of `IMG_0020.png` from studio job `20261028-145745-dc5f64`, published in this repository at the Star Colonel's order of 2026-10-28. It is generated from the Star Colonel's own photo IMG_0020 (`IMG_0020.jpeg` in this folder, the copy with the licence plate blurred).

- This file sha256: `dc42ae2b533c047efa4157434a3fc673da40b0020268048a43611deb748d28f9`
- The job's sidecar follows unchanged, its headings two levels lower

## Sidecar of studio job 20261028-145745-dc5f64

Frame step: outpainted sideways

### IMG_0020.png

- Source working copy: `tmp/media/studio-live2/state/jobs/20261028-145745-dc5f64/input/IMG_0020.png`
- Extender: FLUX 3 Image Klein 5.6B bf16 distilled with the ausboss Outpaint LoRA
- Extender weights: black-forest-labs/flux-3-image-klein: model.safetensors 11,097,404,512 B, ae.safetensors 336,211,292 B, text encoder shards 4,967,229,296 + 3,908,490,048 B merged; ausboss/FLUX-3-Image-Klein-Outpaint-LoRA: flux-3-image-klein-outpaint.safetensors 160,697,104 B
- Extender licence: FLUX Kommunity License v1.0; private non-commercial use permitted, commercial output allowed below the licence revenue threshold
- Prompt: Outpaint the image: replace the solid grey areas with an empty continuation of the same room and scene beyond the frame, keeping the existing picture unchanged. Continue the same floor, the same wall and background and the same soft indoor daylight as the photo, at the same perspective, scale and brightness. The added area holds no person, no child, no face, no hands and no figure; keep every person already in the photo exactly as they are, with the same faces, expressions, hair and clothes.
- Negative prompt: person, child, man, woman, crowd, face, hands, portrait, new person, extra person, second child, mirrored child, reflected child, reflection of a person, different face, changed expression, deformed, distorted, blurry, low quality, text, watermark
- Seed: 42
- Gate: passed; kept seed 42; strangers 0; continuations 0; clipped 0; panels x 0-240 and x 1680-1920
- Gate detectors: face face_yolov8n.pt, ultralytics 8.4.188, conf 0.25, imgsz 1280; person yolo11n.pt class 0 person, ultralytics 8.4.188, conf 0.25, imgsz 1280; rule: stranger: a face or person box wholly inside an added panel and clear of the frame border; continuation: a face crossing into the photo, recorded and not a violation; clipped: a box touching the frame's outer border within 2 px, recorded and not a violation
- Gate strangers: none
- Gate continuations: none
- Gate clipped: none
- Settings: `steps=16`, `cfg=1.0`, `sampler=euler`, `scheduler=simple`, `denoise=1.0`, `lora_strength=1.5`, `render_scale=1.0`
- Frame: pads left 240, right 240, top 0, bottom 8, feather 8 px
- Tone match: per-channel mean and standard deviation over the photo region
- Render: 1920 x 1088 px, cropped to 1920 x 1080 px
- Output: 1920 x 1080 px, ratio 1.7778
- GPU: cuda:0 NVIDIA RTX PRO 6000 Blackwell Max-Q Workstation Edition : cudaMallocAsync
- Render time: 36.5 s (POST /prompt to the finished history entry)
- Peak VRAM: 22.18 GB (nvidia-smi memory.used of the pinned GPU sampled during the render, minus the memory in use before the server started)
- Notes: No mask: the grey-padded frame is the reference latent and the LoRA at strength 1.5 paints the panels; the photo is composited back. The LoRA was trained at 0.94 to 1.96 MP, so both frames are above its tested range; faces are its documented weak area and it does not sharpen.
- Picked file: inputs/IMG_0020.jpeg
- Studio GPU: index 1, NVIDIA RTX PRO 6000 Blackwell Max-Q Workstation Edition, GPU-a44e514a-aa5b-2844-35f1-4be28e1921e5
