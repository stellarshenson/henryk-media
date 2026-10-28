# studio-results.png

Screenshot of the henryk-media studio, the page that `henryk-media studio` serves on 127.0.0.1. It is a browser capture, not a photograph. The only photo in it is IMG_0020, the Star Colonel's own photo, which he authorised on 2026-10-27 for this README. It shows the Jobs panel with one live photo card: the finished frame and the finished clip made from it. Both pictures in the screenshot are generated from IMG_0020.

## Source

- Input: `tmp/media/studio-live/inputs/IMG_0020.jpeg`, a byte copy of `data/external/showcase/IMG_0020.jpeg` (sha256 `1949d902ca7a9726d436b1ae402788f9ec9c84aca2ff0cce3e5e733a9fc7cbf4`), the showcase copy with the parked car's licence plate blurred and the metadata removed (`tmp/workflows/showcase/blur.json`)
- Studio: `.venv/bin/henryk-media studio --port 8520 --state-dir tmp/media/studio-live2/state --input-root tmp/media/studio-live/inputs`
- Both jobs ran locally, on the compute the studio chose automatically, through a ComfyUI server bound to 127.0.0.1, from one Make Live Photo action; the page shows no GPU details; no photo was sent to an external service

## Jobs shown

Step 1 of 2, frame job `20261028-145745-dc5f64`, done:

- Input: `inputs/IMG_0020.jpeg`
- Model: FLUX 3 Image Klein 5.6B bf16 distilled with the ausboss Outpaint LoRA at strength 1.5
- Settings: 16:9 Full HD, 1920x1080, frame step outpainted sideways (side panels x 0-240 and x 1680-1920), cfg 1.0, steps 16, sampler euler, scheduler simple, seed 42
- Person gate: passed with seed 42, 0 strangers in the added panels; the photo band (1440x1080 at x 240) is bit-identical to the scaled photo
- Run: 49 s for the job, 36.5 s render, peak VRAM 22.18 GB

```
Outpaint the image: replace the solid grey areas with an empty continuation of the same room and scene beyond the frame, keeping the existing picture unchanged. Continue the same floor, the same wall and background and the same soft indoor daylight as the photo, at the same perspective, scale and brightness. The added area holds no person, no child, no face, no hands and no figure; keep every person already in the photo exactly as they are, with the same faces, expressions, hair and clothes.
```

Negative prompt: `person, child, man, woman, crowd, face, hands, portrait, new person, extra person, second child, mirrored child, reflected child, reflection of a person, different face, changed expression, deformed, distorted, blurry, low quality, text, watermark`

Step 2 of 2, clip job `20261028-145745-e48830`, done:

- Input: the frame result `jobs/20261028-145745-dc5f64/IMG_0020.png`, scaled to cover 1280x736 and centre-cropped
- Model: MiniMax H3 (FL2VA pruned bf16 transformer, 33B dense), Comfy-Org/MiniMax-H3, revision `e5eb578a89295337b8ff433a035929ce0279e0b6`
- Settings: HD, rendered at 1280x736 and cropped to 1280x720, 5 s, seed 42, steps 20, sampler res_multistep, scheduler simple, no cfg (CFG-distilled checkpoint), no negative prompt; 124 native frames at 24 fps interpolated with FILM fp16 to 150 frames at 30 fps
- Run: 469 s for the job, 450.4 s render, 10.6 s FILM; peak VRAM 82.99 GB during the render and 87.34 GB during FILM, with 20.21 GB of FLUX 3 Klein still resident from the frame job; this run (jobs `20261028-145745-dc5f64` and `20261028-145745-e48830`, 14:57) predates the model-freeing step added on the evening of 2026-10-28, so the 20.21 GB of FLUX 3 Klein it records as resident is expected

```
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] he moves at normal real-time speed and keeps moving through the whole clip; he keeps walking toward the camera at an ordinary pace, about one step per second, holding the red gift box out; in the first two seconds he lifts the gift box a little; by four seconds his smile warms; around six seconds he blinks; in the last two seconds he settles the box back to the same height; Static Shot; the lamp post, the parked car, the building and the trees stay as in the photo, with no signs or lettering; nobody new enters

overall_soundscape: N/A

non_diegetic_music: N/A
```

## Capture

- Size: 864x622 px PNG, 325,073 B, sha256 `eda99ed15d07d1123045f0d879ef04eb9182a6f128457356f08b8bfda48c7cab`
- Date: 2026-10-28T17:26:45+01:00
- Browser: Playwright 1.64.1, headless Chromium 156.0.8078.4, viewport 1440 px wide and as tall as the page (2841 px), light theme
- Crop: the Jobs panel with a 16 px margin
- Clip: played muted to 1.505 s and paused, readyState 4, so the player shows a real frame; it is shown at 355.55x200 px, the 16:9 aspect of the 1280x720 clip
- The page hides the progress line of a finished job, so the card shows the status done and no percent; the job record holds percent 100 for both jobs. The frame step is drawn above the clip because the page orders the two steps of a live photo frame first
- Licence plate: blurred in the input; the frame's parked car was viewed at 12x and no plate character is readable; at 1.5 s the car is behind his shoulder, so no plate pixels are in the clip frame
- MiniMax H3 invented a red banner with letter-like marks above a door on the left building; no character or word is readable
- Script: `tmp/workflows/studio/shots/shoot-nogpu.py`; record `tmp/workflows/studio/nogpu-shots.json`
