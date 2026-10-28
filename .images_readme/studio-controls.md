# studio-controls.png

Screenshot of the henryk-media studio, the page that `henryk-media studio` serves on 127.0.0.1. It is a browser capture, not a photograph. The only photo in it is IMG_0020, the Star Colonel's own photo, which he authorised on 2026-10-27 for this README. It shows the controls column: the photo picker with its preview, the Frame panel, the Clip panel and the action bar. The results of these settings are in `studio-results.png`.

## Source

- Input: `tmp/media/studio-live/inputs/IMG_0020.jpeg`, a byte copy of `data/external/showcase/IMG_0020.jpeg` (sha256 `1949d902ca7a9726d436b1ae402788f9ec9c84aca2ff0cce3e5e733a9fc7cbf4`), the showcase copy with the parked car's licence plate blurred and the metadata removed (`tmp/workflows/showcase/blur.json`)
- Studio: `.venv/bin/henryk-media studio --port 8520 --state-dir tmp/media/studio-live2/state --input-root tmp/media/studio-live/inputs`; the picker listed only `inputs/IMG_0020.jpeg`
- The two jobs of the live run reloaded from disk; no job ran during the capture, and no photo was sent to an external service

## Page state shown

- Compute: the studio chooses the compute itself; the page shows no GPU details; a crop or a scale needs no GPU
- Photo: `inputs/IMG_0020.jpeg` selected, with its preview
- Frame: 16:9, Full HD 1080 lines, cfg 1.0, the outpaint prompt and the negative prompt, and the note that the negative prompt has no effect at cfg 1.0
- Clip: clip input `IMG_0020.jpeg`; the MiniMax H3 prompt fields Action, Camera (`Static Shot`), Hold, Soundscape (empty, sent as N/A) and Music (`N/A`); the final prompt the job sends; 5 s, HD 720 lines, seed 42
- Action bar: Make Live Photo, Make Frame and Make Clip
- These are the fields the studio saved when the live run submitted Make Live Photo for frame job `20261028-145745-dc5f64` (FLUX 3 Image Klein 5.6B with the ausboss Outpaint LoRA, 16:9 Full HD 1920x1080) and clip job `20261028-145745-e48830` (MiniMax H3, HD 1280x720, 5 s, seed 42); the prompt texts, models and run settings are listed in `studio-results.md`

## Capture

- Size: 552x2726 px PNG, 365,103 B, sha256 `69c4a174ca82c52ceb1b5a0fd12271c953d0d45b6384ceee6b42f58fbdd4ec58`
- Date: 2026-10-28T17:26:44+01:00
- Browser: Playwright 1.64.1, headless Chromium 156.0.8078.4, viewport 1440 px wide and as tall as the page (2841 px), light theme
- Crop: the controls column with a 16 px margin, from below the page header to the end of the action bar; at README width a 1440-wide capture would shrink the 12 to 14 px text below reading size, so the capture is the column at its natural size, and the header subtitle runs into the Jobs column, so the header is not in the crop
- Every textarea was enlarged to the height of its text, as its resize handle allows, so no prompt is cut
- Licence plate: blurred in the input; the preview was viewed at 10x and no plate character is readable; the full-size frame's parked car is checked at 12x in `studio-results.md`
- Script: `tmp/workflows/studio/shots/shoot-nogpu.py`; record `tmp/workflows/studio/nogpu-shots.json`
