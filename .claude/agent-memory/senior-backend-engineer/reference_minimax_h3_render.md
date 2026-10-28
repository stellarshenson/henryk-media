---
name: minimax-h3-render
description: MiniMax H3 image-to-video - per-clip time and VRAM, no negative conditioning, FILM drops the generated audio
metadata:
  type: reference
---

Rendered 2026-10-25 on the RTX PRO 5000 72 GB (UUID GPU-1223ff00...), 768x1024, 124 frames at
24 fps, 20 res_multistep steps, seed 42; FILM to 150 frames at 30 fps.

- 435.8 s, 473.7 s and 469.4 s per clip, each including a full model load
- Peak 63.2 GB on the first clip, 66.1 GB on the later two, about 10 GB still free
- The graph has no negative conditioning input (CFG-distilled, one BasicGuider with positive
  only); record the intended negative prompt with negative_prompt_applied=no instead of applying it
- FILM re-encodes video only, so delivered clips have no audio track even though the graph decodes audio
- ComfyUI leaves input/3d, output/exp_data and temp/temp as empty directories; no files remain

Related: [[wan22-fallback]]
