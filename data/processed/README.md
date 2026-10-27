# data/processed

Final, canonical datasets for modeling.

Generated media enters this tree only after the Star Colonel has viewed it and judged it good, or when he declares the run production before viewing it. Every output carries a `<stem>.md` sidecar naming its source file, model, prompt and settings; an output from a model call also carries `checkpoints/<stem>.json` measurements. Keep this index current; see [../README.md](../README.md).

## Datasets

- `henryk-urodziny-2026/extended/` - the source photos in `data/external/henryk-urodziny-2026/images/` converted to 4:3 and 16:9 frames; `4x3/` holds 11 PNGs at 1280 x 960, nine extended with FLUX 3 Image Klein and its outpaint LoRA and two already 4:3, scaled with no model call; `16x9/` holds 11 FLUX extensions at 1280 x 720; each `<stem>.png` has a `<stem>.md` sidecar and, for model-called frames, `checkpoints/<stem>.json`; `grid-4x3.png` and `grid-16x9.png` are 2240 x 1344 contact sheets
- `henryk-urodziny-2026/minimax-h3/` - 10 MiniMax H3 clips, variant `production-4x3`, 1024 x 768, 150 frames at 30 fps (5.00 s), animated from `extended/4x3/<stem>.png`; `<stem>.mp4` with `<stem>.md` sidecar and `checkpoints/<stem>.json`
- `henryk-urodziny-2026/minimax-h3-6s/` - 6 MiniMax H3 clips, variant `production-4x3-6s`, 1024 x 768, 180 frames at 30 fps (6.00 s), from the same sources and convention
- `henryk-urodziny-2026/minimax-h3-10s/` - 10 MiniMax H3 clips, variant `production-4x3-10s`, 1024 x 768, 300 frames at 30 fps (10.00 s), from the same sources and convention
