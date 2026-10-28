---
name: reference-liveportrait-repo
description: LivePortrait GitHub repository moved from KwaiVGI to KlingAIResearch; the GitHub API needs redirect-following (curl -L)
metadata:
  type: reference
---

`KwaiVGI/LivePortrait` redirects to `KlingAIResearch/LivePortrait` (seen 2026-10-24). The GitHub contents API answers "Moved Permanently" without `curl -L`. Bundled driving examples are under `assets/examples/driving/` (12 mp4 files). LICENSE is MIT text plus a note that InsightFace models are non-commercial, so GitHub reports the licence as "Other".

`driving_option="expression-friendly"` has no effect in the human pipeline with relative motion and a still photo: `calc_motion_multiplier(x_s, x_d_0_new)` compares the photo's keypoints with themselves, so m = 1 (live_portrait_pipeline.py lines 389-395; only the animal pipeline uses the real driving frame). Do not describe it as scaling motion to the photo's face.
