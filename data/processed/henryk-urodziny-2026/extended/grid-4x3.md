# grid-4x3.png

- Kind: contact sheet, no model call - the 11 extended 4:3 frames in this folder composed into one labelled sheet; each tile's model, prompt, settings and gate record live in that frame's own sidecar `4x3/<stem>.md`
- Composer: `tmp/workflows/image-extender/review_all.py` (PIL contact-sheet code in `henryk_media.imaging.grids`), no model call
- Sheet: 2240 x 1344 px, four columns by three rows; each tile is its frame fitted into a 560 x 420 px box with a 28 px label bar; the twelfth cell is empty
- Extender: FLUX 3 Image Klein 5.6B bf16 distilled with the ausboss Outpaint LoRA, for nine tiles; IMG_0020 and IMG_8779 are LANCZOS scales with no model call because those photos are already 4:3
- Extender weights: black-forest-labs/flux-3-image-klein: model.safetensors 11,097,404,512 B, ae.safetensors 336,211,292 B, text encoder shards 4,967,229,296 + 3,908,490,048 B merged; ausboss/FLUX-3-Image-Klein-Outpaint-LoRA: flux-3-image-klein-outpaint.safetensors 160,697,104 B
- Extender licence: FLUX Kommunity License v1.0; private non-commercial use permitted, commercial output allowed below the licence revenue threshold
- Prompt (nine tiles): Outpaint the image: replace the solid grey areas with an empty continuation of the same room and scene beyond the frame, keeping the existing picture unchanged. Continue the same floor, the same wall and background and the same soft indoor daylight as the photo, at the same perspective, scale and brightness. The added area holds no person, no child, no face, no hands and no figure; keep every person already in the photo exactly as they are, with the same faces, expressions, hair and clothes.
- Negative prompt (nine tiles): person, child, man, woman, crowd, face, hands, portrait, new person, extra person, second child, mirrored child, reflected child, reflection of a person, different face, changed expression, deformed, distorted, blurry, low quality, text, watermark
- Settings (nine tiles): `steps=16`, `cfg=1.0`, `sampler=euler`, `scheduler=simple`, `denoise=1.0`, `lora_strength=1.5`, `render_scale=1.0`, `seed=42`
- Tile output: 1280 x 960 px each, ratio 1.3333
- Gate: passed on all nine model-called tiles; strangers 0; continuations recorded on IMG_8564 (2) and IMG_8840 (1)
- Render time: not applicable (no model call)
- Peak VRAM: not applicable (no model call)

Tiles, left to right and top to bottom:

| Position | Frame | Source photo | Made by |
|---:|---|---|---|
| 1 | `4x3/IMG_0020.png` | `data/external/henryk-urodziny-2026/images/IMG_0020.jpeg` | LANCZOS scale, photo already 4:3 |
| 2 | `4x3/IMG_7645.png` | `data/external/henryk-urodziny-2026/images/IMG_7645.JPG` | FLUX 3 Klein + Outpaint LoRA |
| 3 | `4x3/IMG_7666.png` | `data/external/henryk-urodziny-2026/images/IMG_7666.JPG` | FLUX 3 Klein + Outpaint LoRA |
| 4 | `4x3/IMG_7667.png` | `data/external/henryk-urodziny-2026/images/IMG_7667.JPG` | FLUX 3 Klein + Outpaint LoRA |
| 5 | `4x3/IMG_8076.png` | `data/external/henryk-urodziny-2026/images/IMG_8076.JPG` | FLUX 3 Klein + Outpaint LoRA |
| 6 | `4x3/IMG_8564.png` | `data/external/henryk-urodziny-2026/images/IMG_8564.jpg` | FLUX 3 Klein + Outpaint LoRA |
| 7 | `4x3/IMG_8716.png` | `data/external/henryk-urodziny-2026/images/IMG_8716.JPG` | FLUX 3 Klein + Outpaint LoRA |
| 8 | `4x3/IMG_8732.png` | `data/external/henryk-urodziny-2026/images/IMG_8732.JPG` | FLUX 3 Klein + Outpaint LoRA |
| 9 | `4x3/IMG_8779.png` | `data/external/henryk-urodziny-2026/images/IMG_8779.JPG` | LANCZOS scale, photo already 4:3 |
| 10 | `4x3/IMG_8828.png` | `data/external/henryk-urodziny-2026/images/IMG_8828.JPG` | FLUX 3 Klein + Outpaint LoRA |
| 11 | `4x3/IMG_8840.png` | `data/external/henryk-urodziny-2026/images/IMG_8840.jpg` | FLUX 3 Klein + Outpaint LoRA |
