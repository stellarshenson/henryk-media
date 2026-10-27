# Gate and output

`PersonGate` classifies every detection on the composited frame, and each tile's sidecar and checkpoint record the verdict, geometry and measurements.

## Frame geometry

- `Geometry.for_aspect(photo_size, aspect, feather=8)` in `src/henryk_media/imaging/composite.py`
- `BASE_WIDTH` 1280; `height = round(1280 / aspect)`, 960 at 4:3 and 720 at 16:9
- `scaled_width = round(photo_width * height / photo_height)`; the photo is resized once with LANCZOS and centred
- `pad_left = (1280 - scaled_width) // 2`; the odd column and the stride padding go to `pad_right`
- `pad_top` 0; `pad_bottom = round_up(height, 8) - height`
- `VAE_STRIDE` 8; every render side rounds up to a multiple of 8, and `composite.crop` keeps the top-left `geometry.width x geometry.height`
- Feather 8 px (`FEATHER` in `src/henryk_media/imaging/extender.py`); `interior_matches` proves every pixel at least 8 px inside the photo border is bit-identical to the source
- Tone match shifts and scales each RGB channel to the scaled photo's mean and standard deviation over the photo region

## Person gate

- `PersonGate` in `src/henryk_media/imaging/gate.py`, CPU, weights `models/photo-animation/ComfyUI/models/ultralytics`
- Detectors `face_yolov8n.pt` and COCO `yolo11n.pt` class 0 person
- Confidence 0.25 (`CONFIDENCE`), imgsz 1280 (`IMAGE_SIZE`), `FULLY_INSIDE` 1 - 1e-6, `BORDER_TOLERANCE` 2.0 px
- Panels: x 0 to `photo_left`, and `photo_left + photo_width` to `frame_width`
- Stranger: a box wholly inside a panel (`inside >= 1 - 1e-6`) and clear of the frame border; fails the frame and advances the seed
- Continuation: a face box crossing the photo edge into a panel (`0 < inside < 1 - 1e-6`), clear of the frame border; recorded and passes
- Clipped: any box within 2 px of the frame's outer border; recorded and passes, checked before the stranger rule
- A face wholly inside the photo, and a person that touches the photo but not the frame border, are not recorded
- Both detectors load once and are reused for every tile

## Sidecar and checkpoint

- Sidecar `<output stem>.md` beside the PNG; checkpoint `checkpoints/<stem>.json` beside it (`provenance.checkpoint_path`)
- Sidecar records the source, extender, weights, licence, prompt, negative prompt, seed, gate lines, settings, frame pads and feather, tone match, render and output sizes, GPU, seconds and peak VRAM
- `provenance.gate_lines` records the verdict, kept seed, detectors, rule, panels and every stranger, continuation and clipped box
- The checkpoint holds the same `ExtendResult` and is the restore key
- `extend()` returns the stored result when extender, aspect, prompt, negative prompt, licence, start seed, detector signatures, geometry and settings all match
- A re-render moves the previous PNG, sidecar and checkpoint to the trash first
- Seconds are POST `/prompt` to the finished history entry; peak VRAM is nvidia-smi memory.used of the pinned GPU minus memory used before the server started

## Grid and re-score

- `grids.contact_sheet(grid, path)` writes a labelled PNG and a `.md` index beside it, one tile per frame
- Re-score without rendering: `gate.check(frame, pad_left, photo_width_in_frame)`, rewrite with `provenance.save_extend`, rebuild the grids
- `.venv/bin/python tmp/workflows/image-extender/rescore_tiles.py` prints the verdicts only
- Add `--write` to persist the gate record, sidecars, both grids and `tmp/workflows/image-extender/rescore-border.json`

## Measured

- Production run 2026-10-25 07:30: 11 photos, 22 frames, 20 generated, 2 scaled only, 0 strangers, 7 continuations, 0 gate failures
- Render seconds: 4:3 10.56-12.99, 16:9 8.79-9.67, first frame 71.79; peak VRAM 20.21-21.32 GB
- Bench re-score at 1280: flux3-klein 0 strangers, 2 continuations, 5 clipped in both aspects; 13 of 16 tiles passed overall (`rescore-border.json`)
