---
name: verify-child-media-locally
description: Never open Henry's photos or clips with the Read tool; verify frames with local CPU measurements and state the visual limitation
metadata:
  type: feedback
---

Never open a photo or clip of Henry with the Read tool or any other tool that sends its bytes to the model serving the session. Verify the frames with local computation instead.

**Why:** The project treats the child's media as personal data. The Read tool passes image bytes to the remote model, and a workflow script's instruction to view frames is not the Star Colonel's approval for that service. The build agent for LTX-2.5 (2026-10-25) and the round-1 verifier both hit this and declined.

**How to apply:** Extract the frames into `tmp/workflows/image-to-video/verify-frames-<key>/` with OpenCV, then measure inter-frame difference, border versus face optical flow, SIFT/ECC background alignment, and face presence with the YOLO face model at `models/photo-animation/ComfyUI/models/ultralytics/face_yolov8n.pt` on CPU (`CUDA_VISIBLE_DEVICES=""`). Record in the checkpoint that distorted hands, added text and visual identity were not assessed. Related: [[reference_minimax_h3_render]].
