# studio.png

Screenshot of the henryk-media studio, the page that `henryk-media studio` serves on 127.0.0.1. It is a browser capture, not a photograph. The only photo in it is IMG_0020, the Star Colonel's own photo, which he authorised on 2026-10-27 for this README. The two pictures in the screenshot are generated from IMG_0020: the first frame of the MiniMax H3 clip and the 16:9 outpaint result.

## Source

- Input: `tmp/media/studio-live/inputs/IMG_0020.jpeg`, a byte-exact copy of `data/external/henryk-urodziny-2026/images/IMG_0020.jpeg` (sha256 `006468b0fdcac615d31b214d2248c7d1e15f8d8a075a6f9256d3949a4f43e17d`), 4896x3672 after EXIF orientation
- Studio: `.venv/bin/henryk-media studio --port 8520 --state-dir tmp/media/studio-live/state --input-root tmp/media/studio-live/inputs`; the picker listed only `inputs/IMG_0020.jpeg`
- Both jobs ran locally on GPU 2 (NVIDIA RTX PRO 5000 72GB Blackwell, `GPU-1223ff00-ce71-874f-592e-a4429e9f47ba`) through a ComfyUI server bound to 127.0.0.1; no photo was sent to an external service

## Jobs shown

Video job `20261027-223015-d78a61`, progress 100 %, stage done:

- Input: the outpaint result `jobs/20261027-222824-252e7c/IMG_0020.png`
- Model: MiniMax H3 (FL2VA pruned bf16 transformer, 33B dense), Comfy-Org/MiniMax-H3, revision `e5eb578a89295337b8ff433a035929ce0279e0b6`
- Settings: 1024x768, 5 s, seed 42, steps 20, sampler res_multistep, scheduler simple, no cfg (CFG-distilled checkpoint), no negative prompt, 124 native frames at 24 fps interpolated with FILM fp16 to 150 frames at 30 fps
- Run: 440 s for the job, 380.9 s render, 9.7 s FILM, peak VRAM 74.43 GB
- MiniMax H3 stretched the 1280x720 input to 1024x768 (its first frame is a plain stretch to the canvas), so the clip is squeezed horizontally

```
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] he moves at normal real-time speed and keeps moving through the whole clip; he keeps walking toward the camera at an ordinary pace, about one step per second, holding the red gift box out; in the first two seconds he lifts the gift box a little; by four seconds his smile warms; around six seconds he blinks; in the last two seconds he settles the box back to the same height; Static Shot; the lamp post, the parked car, the building and the trees stay as in the photo, with no signs or lettering; nobody new enters

overall_soundscape: N/A

non_diegetic_music: N/A
```

Outpaint job `20261027-222824-252e7c`, progress 100 %, stage done:

- Input: `inputs/IMG_0020.jpeg`
- Model: FLUX 3 Image Klein 5.6B bf16 distilled with the ausboss Outpaint LoRA at strength 1.5
- Settings: 16:9 at 1280 px → 1280x720, side panels of 160 px, cfg 1.0, steps 16, sampler euler, scheduler simple, seed 42
- Person gate: passed with seed 42, 0 strangers in the added panels
- Run: 33 s for the job, 21.3 s render, peak VRAM 21.01 GB
- A 4:3 request was refused before this job, because IMG_0020 is already 4:3 and leaves nothing to extend

```
Outpaint the image: replace the solid grey areas with an empty continuation of the same room and scene beyond the frame, keeping the existing picture unchanged. Continue the same floor, the same wall and background and the same soft indoor daylight as the photo, at the same perspective, scale and brightness. The added area holds no person, no child, no face, no hands and no figure; keep every person already in the photo exactly as they are, with the same faces, expressions, hair and clothes.
```

Negative prompt: `person, child, man, woman, crowd, face, hands, portrait, new person, extra person, second child, mirrored child, reflected child, reflection of a person, different face, changed expression, deformed, distorted, blurry, low quality, text, watermark`

## Capture

- Size: 1440x900 px PNG, 655,535 B
- Date: 2026-10-27T22:45:09+01:00
- Browser: Playwright 1.64.1, headless Chromium build 1248, viewport 1440x900, light colour scheme
- Page state: GPU 2 selected, `inputs/IMG_0020.jpeg` selected; both controls lie above the captured area, and the job titles name GPU 2 and IMG_0020
- Framing: the full page is 3133 px tall, above the 2400 px limit for a full-page capture, so the PNG is the viewport scrolled to the top of the Jobs panel
- Script: `tmp/workflows/studio/screenshot/shoot.py`
