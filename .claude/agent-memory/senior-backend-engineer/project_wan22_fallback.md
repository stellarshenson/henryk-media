---
name: wan22-fallback
description: Wan2.2 is the fallback image-to-video model; discard it if LTX-2.5 and MiniMax H3 look believable
metadata:
  type: project
---

The Star Colonel said "if they are good, we can discard wan 2.2" (2026-10-25). LTX-2.5 and
MiniMax H3 are the preferred image-to-video models; Wan2.2 stays only if both fail his
believability bar ([[live-photo-believability-bar]]).

**Why:** Wan2.2 takes about 80 minutes per 5 s clip at the native settings (4791 s smoke), against
450 s for MiniMax H3 and 468 s for LTX-2.5, so it is roughly ten times slower.

**How to apply:** Do not discard Wan2.2 weights, notebook 05 or its output until the Star Colonel
has judged the LTX-2.5 and MiniMax H3 clips. Discard them only on his word.
