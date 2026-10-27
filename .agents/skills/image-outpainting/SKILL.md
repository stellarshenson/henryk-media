---
name: image-outpainting
description: Extend a photo sideways into a 4:3 or 16:9 frame with FLUX 3 Klein and its outpaint LoRA, preserving the photo's pixels and gating invented people. Use when asked to outpaint, widen or extend a photo to 4:3 or 16:9, fit a landscape frame, re-score or re-grid an extender run, or when FLUX 3 Klein or the image-extender notebook is named.
---

# Image outpainting

Extend a photo sideways with FLUX 3 Klein, its outpaint LoRA and a no-new-people gate; only the side panels are generated and the photo's own pixels are pasted back. The caller names the output path; `extend` writes the PNG and its `.md` sidecar there, and the checkpoint under `checkpoints/<stem>.json` in the same folder.

## Frames

- 4:3 is exactly 1280x960; 16:9 exactly 1280x720 (`BASE_WIDTH`, `Geometry.for_aspect`, `src/henryk_media/imaging/composite.py`)
- Photo scaled once to the frame height with LANCZOS and centred; only the sides are padded and generated
- Side pad is half the difference, plus VAE stride padding on the right; the saved frame crops to the exact size
- A photo already at the target ratio is scaled only, no model call (`tmp/workflows/image-extender/extend_all.py` branches on zero side pads; `extend()` itself always renders)
- Tone match shifts and scales each RGB channel to the scaled photo's mean and standard deviation over the photo region
- Paste-back uses an 8 px feather; every pixel at least 8 px inside the photo border is bit-identical to the source (`interior_matches`)
- Frame arithmetic and output paths: `references/gate-and-output.md`

## Model

- `flux3-klein`: `black-forest-labs/flux-3-image-klein` plus the `ausboss/FLUX-3-Image-Klein-Outpaint-LoRA` at strength 1.5
- steps 16, cfg 1.0, euler, simple, denoise 1.0, render scale 1.0
- Seeds 42 upward through 47, six attempts; the first passing frame is kept, otherwise the last frame is kept and marked failed
- Out of memory: retry at 0.71 then 0.5 render scale, largest fitting size kept
- Weights, text encoder, prompts, licence and the server start command: `references/extender-recipe.md`

## Person gate

- `PersonGate` (`src/henryk_media/imaging/gate.py`) on the CPU; detectors `face_yolov8n.pt` and COCO `yolo11n.pt` class 0 person, confidence 0.25, imgsz 1280
- Stranger: a box wholly inside an added panel and clear of the frame border; fails the frame and advances the seed
- Continuation: a face box crossing the photo edge into a panel, clear of the frame border; recorded and passes
- Clipped: a box within 2 px of the frame's outer border; recorded and passes
- The sidecar records the verdict, seed, detectors, panels and every box
- Thresholds, weights folder and sidecar lines: `references/gate-and-output.md`

## Sequence

1. Working copy: EXIF orientation (`ImageOps.exif_transpose`), RGB, downscale only when the long edge exceeds 2048 px, PNG (`tmp/workflows/image-extender/prepare_all.py`)
2. Pin the GPU before torch import: `CUDA_DEVICE_ORDER=PCI_BUS_ID`, `CUDA_VISIBLE_DEVICES` to the UUID in `references/extender-recipe.md`, nvidia-smi index 1
3. Start the server: `Setup.load("tmp/workflows/image-extender/setup-extender.json")`, then `ComfyServer(setup)`; port 8189; exact command in `references/extender-recipe.md`
4. Run one frame: `registry.extender("flux3-klein")`, `PersonGate(weights_dir)`, `extend(server, model, source, aspect, output, PROMPT, NEGATIVE_PROMPT, gate, seed=42)` with aspect `4x3` or `16x9`
5. `extend()` scales, renders, tone-matches, pastes back, crops, gates, sweeps seeds and writes the PNG, sidecar and checkpoint
6. `grids.contact_sheet(grid, path)` writes a labelled PNG and `.md` index, one tile per frame
7. Re-score without rendering: `gate.check(frame, pad_left, photo_width_in_frame)`, rewrite with `provenance.save_extend`, rebuild the grids; command in `references/gate-and-output.md`

## Fault modes

- Invented people in the added panels: a stranger, so the next seed; after six the last frame stays marked failed
- A face given to a person cut off at the photo edge: a continuation, recorded and passing
- A border sliver or easel leg read as a person: clipped within 2 px of the outer border, recorded and passing

<!-- improved 2026-10-25 | body 467→455w / 56→58L | benchmark n/a (not-requested) | via improve-skill -->
<!-- improved 2026-10-25 | body 455→797w / 58→68L | benchmark n/a (not-requested) | via improve-skill -->
<!-- improved 2026-10-27 | body 807→538w / 63→46L | benchmark n/a (not-requested) | via improve-skill -->
