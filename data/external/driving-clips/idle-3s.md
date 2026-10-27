# idle-3s.mp4

A 3-second driving clip for LivePortrait, cut from the bundled example `d9.mp4`.

- Source file: `data/external/driving-clips/liveportrait/d9.mp4` (sha256 `9a414aa1d547be35306d692065a2157434bf40a6025ba8e30ce12e5bb322cc33`)
- Source URL: https://raw.githubusercontent.com/KlingAIResearch/LivePortrait/main/assets/examples/driving/d9.mp4 (the repository `KwaiVGI/LivePortrait` now redirects to `KlingAIResearch/LivePortrait`; last commit to the folder `a19c3e15fbca2571e7a48fd68889e0956409d05b`, 2024-08-19)
- Licence: MIT, as part of the LivePortrait repository (`LICENSE`, copyright 2024 Kuaishou Visual Generation and Interaction Center)
- Cut points: source frames 372 to 461 inclusive, 12.400 s to 15.400 s (end exclusive), 90 frames
- Format: 512 x 480 px (SAR 15:16, display aspect 1:1), 30 fps (same as source), H.264 CRF 12, yuv420p, audio removed
- sha256: `36efc25f42fce580ccfbcd5a47a6a4a8f3822180c922018c22b3d0b2405fde26`

## Why this clip

- `d9.mp4` is the only bundled clip with a stretch of near-neutral face without talking: three natural blinks (about 0.27-0.67 s, 1.70-1.90 s and 2.50-2.70 s into the cut), a closed-lip slight smile (about 1.0-1.5 s), and a small forward head dip during the first blink
- The first frame is a frontal face with open eyes and a closed mouth, which LivePortrait uses as the reference for relative motion
- Limitation: the last 0.3 s (cut frames 81 to 89) contain the onset of an eyebrow raise with pursed lips. The calm stretch without it is source frames 371 to 447 (2.57 s); a full 3 s needs either this onset at the end or a blink in progress at the start
