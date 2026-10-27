# Henryk Media - Photo animation model selection v1

Status: DRAFT for internal review, 2026-10-24.

## Contents

- [1. Use case and bar](#1.-Use-case-and-bar)
- [2. Recommendation](#2.-Recommendation)
  - [2.1 Test models](#2.1-Test-models)
  - [2.2 Reserves](#2.2-Reserves)
  - [2.3 Decision rule](#2.3-Decision-rule)
- [3. Candidate comparison](#3.-Candidate-comparison)
- [4. Excluded models](#4.-Excluded-models)
- [5. Test plan](#5.-Test-plan)
  - [5.1 Shared preparation](#5.1-Shared-preparation)
  - [5.2 LivePortrait test](#5.2-LivePortrait-test)
  - [5.3 FantasyPortrait test](#5.3-FantasyPortrait-test)
  - [5.4 FlashPortrait test](#5.4-FlashPortrait-test)
  - [5.5 PerformRecast reserve](#5.5-PerformRecast-reserve)
  - [5.6 HunyuanPortrait reserve](#5.6-HunyuanPortrait-reserve)
- [6. Caveats and confidence](#6.-Caveats-and-confidence)
- [7. Sources](#7.-Sources)

## 1. Use case and bar

The goal is a clip of about 3 s that plays once, like an iPhone Live Photo, made fully offline from one upright 3:4 phone photo of a 3-4 year old child. The motion must stay subtle (a blink, breathing, a slight head turn or smile, a little hair movement), and every face must stay exactly as in the photo, with no seam where a face-only method pastes the face back. Only purpose-built photo or portrait animation models with downloadable weights qualify, judged on three test photos: (a) a smiling close-up with a jar, 1034x1374; (b) one child between two others, three faces, 962x1278; (c) a seated child with curly hair drawing, 1500x2000.

## 2. Recommendation

This section ranks the three models to test and the two reserves, with the reason for each position. Scores are the shortlist's assessment out of 100 (idle motion 25, identity 25, quality evidence 15, test photos 15, local setup 15, licence 5), not measurements. The fact verifier's corrections did not change the order.

| Rank | Model | Base model | Score | Download | GPU |
|---|---|---|---:|---:|---|
| Test 1 | LivePortrait via ComfyUI-AdvancedLivePortrait | Own implicit-keypoint warping network, not diffusion | 84 | 0.53 GB | 2 |
| Test 2 | FantasyPortrait | Wan2.1-I2V-14B-720P | 64 | 86.3 GB | 1 |
| Test 3 | FlashPortrait | Wan2.1-I2V-14B-720P, attention modules trained | 57 | 58.3 GB extra | 2 |
| Reserve 1 | PerformRecast | Retrained LivePortrait networks | 58, indicative | about 1.2 GB | 0 |
| Reserve 2 | HunyuanPortrait | Stable Video Diffusion img2vid-xt | 44 | about 7.6 GB | 2 |

### 2.1 Test models

The three test models cover two identity mechanisms: LivePortrait warps the photo's own pixels, and FantasyPortrait and FlashPortrait regenerate the whole frame on Wan2.1-I2V-14B.

- **LivePortrait, rank 1**:
  - It is the only candidate that makes idle motion with no driving input. The AdvancedLivePortrait node interpolates between edited expressions [3]
  - It warps the photo's own face pixels and pastes a 512x512 render back with a soft mask. Every pixel outside the mask stays original [1][3]
  - Identity: it is the best baseline in three of four identity columns of PerformRecast's CVPR 2026 tables, with self-reenactment CSIM 0.8008, best of 17 baselines [26]. In six earlier papers' tables it is second in three and mid-table in three, never last [29][40][42][43][56]
  - It downloads 0.53 GB and needs no compiled CUDA op [3][5]
  - Its clips become the driving videos for every other model, so it runs first
  - Risk: a later paper reports discontinuities at the paste-back [13], and the face is rendered at 512x512, so a close-up face may look softer than the rest (inference)
- **FantasyPortrait, rank 2**:
  - It is the only model trained and evaluated for several faces in one photo. `infer_multi.py` drives each face from its own video [13][14], which fits photo (b)
  - It regenerates the whole frame, so hair and body can move, which fits photo (c) (medium)
  - Quality in FlashPortrait's table of 8 methods: FID 3rd and FVD 2nd on VoxCeleb2 and VFHQ, FID 6th and FVD 3rd on Hard100, best on no column [19]
  - Identity: the only numbers from outside its own paper are PerformRecast's. Cross-reenactment CSIM is 0.7694, second of 17 baselines; self-reenactment CSIM is 0.7368 against LivePortrait's 0.8008; self-reenactment FID and FVD are 42.60 and 446.28 against LivePortrait's 21.32 and 192.02 [26]
  - Risk: regeneration at 720x960 can change the child's face, and an open issue reports blurry output with a grid pattern [15]
- **FlashPortrait, rank 3**:
  - It tests the whole-frame mechanism a second time, with identity-focused training (only the DiT attention modules trained), face-only PD-FGC driving and 4-step sampling [19][20]
  - It has the best FID, FVD, AED and APD in its own Table 1, but its identity evidence is only its own user study of 30 samples [19]
  - It shares the 82.2 GB Wan2.1 base with FantasyPortrait, so it adds 58.3 GB [16][21]
  - It drives one face only [20]
  - It stays above PerformRecast despite PerformRecast's indicative score of 58. PerformRecast repeats test 1's crop-and-paste mechanism, cannot turn the head, takes a video and not a photo in the released code, and only its own paper supports it [26][28]

### 2.2 Reserves

Each reserve covers a failure that the test models cannot cover.

- **PerformRecast, reserve 1** - it retrains LivePortrait's networks and separates facial and non-facial regions to reduce misalignment at the face boundary [27]. Its authors tested it on Python 3.12, CUDA 12.8 and PyTorch 2.11 [28]. Test it if LivePortrait shows a seam. It takes the place of Wan-Animate, which left the reserves (section 4)
- **HunyuanPortrait, reserve 2** - it regenerates only a 512x512 head-and-shoulders square and pastes it back with a soft mask [30], a third identity mechanism. Its code and model licences allow only academic, research and education use [30], so it runs only if the Star Colonel accepts that licence for private family use

### 2.3 Decision rule

The rule below decides which model runs next after each result.

- If LivePortrait shows a seam or a softer face on photo (a), FantasyPortrait becomes first and PerformRecast is tested
- If FantasyPortrait visibly changes the child's face on all three photos, FlashPortrait carries the same risk from the same base model and the same whole-frame regeneration. Its 58.3 GB download then waits for the Star Colonel's word
- If LivePortrait shows a seam and both Wan2.1 models change the face, HunyuanPortrait is next, subject to the licence decision

## 3. Candidate comparison

This table compares all 23 in-scope candidates against the bar. The last column gives each candidate's role in this selection.

| Model (base) | Driving input | What moves | Multi-face | Licence | VRAM | Runtime path | Live-photo fit | Sources |
|---|---|---|---|---|---|---|---|---|
| LivePortrait (own warping network) | None with AdvancedLivePortrait keyframes; `.pkl` template or video | Face crop, pasted back; rest of the photo keeps its pixels | One per run (centre face); three by the rectangle method | MIT weights; node code has no licence file | Not published; about 4 GB (inference) | ComfyUI + AdvancedLivePortrait, Python 3.13, cu130 torch | Test 1: idle motion with no driving input, original pixels kept | [1][2][3][6] |
| FantasyPortrait (Wan2.1-I2V-14B-720P) | Driving video per face | Whole frame regenerated at 720x960 | Yes, trained for it | Apache-2.0 | 40 GB at full load on A100, resolution not stated | Official repo, Python 3.12, cu128 torch | Test 2: only multi-face model; face may change | [13][14][15] |
| FlashPortrait (Wan2.1-I2V-14B-720P) | Driving video | Whole frame regenerated | One face | Apache-2.0 | About 60 GB at full load, 10 s at 720x1280 | Official `fast_infer.py`, Python 3.12, cu128 torch | Test 3: identity-focused whole-frame model | [19][20][21] |
| PerformRecast (retrained LivePortrait networks) | Source video plus driving video | Face expression only, pasted back; head pose from the source | One per run (`face_index`) | MIT code; InsightFace non-commercial (accepted) | Not published | Official `inference.py`, Python 3.12, torch 2.11 cu128 | Reserve 1: seam fallback; no head turn | [26][27][28] |
| HunyuanPortrait (SVD img2vid-xt) | Driving video | 512x512 head-and-shoulders square, pasted back | One face | Academic, research and education only | Under 20 GB for 4 s on RTX 3090 | Official `inference.py`, Python 3.12, cu128 torch | Reserve 2: licence decision needed | [29][30][31] |
| LongCat-Video-Avatar 1.5 (LongCat-Video DiT) | Audio (a silent track for idle) plus text and reference image | Whole frame at 480P or 720P | Two people documented, three not | MIT | 46,827 MiB peak, one tester | Official repo; torch 2.6.0+cu124 and flash_attn pins; no SDPA fallback; examples on 2 GPUs | Not picked: own report only; tester saw an added hand gesture; 158 GB download | [35][36][37][38] |
| SadTalker (3DMM plus face renderer) | Audio; idle mode with silent audio and blinks | Face crop, pasted back with `--still --preprocess full` | Not documented | Apache-2.0 | Not published | Official CLI; Python 3.8, torch 1.12.1+cu113 | Not picked: pin has no sm_120 kernels; dated 256/512 renderer | [39] |
| PersonaLive (SD image-variations) | Driving video | 512x512 crop; no paste-back documented | Not documented | Apache-2.0 tag; README says academic research only | 12 GB, streaming offline mode | Official `inference_offline.py`, Python 3.10, xFormers off | Not picked: 512 crop; added glasses reported; ID-SIM 0.698 against LivePortrait 0.723 | [40] |
| LIA-X (own autoencoder) | Driving video or control panel | Face crop at fixed 256 or 512; no paste-back documented | Not documented | CC BY-NC 4.0 | Not published | Official repo, Python 3.10 | Not picked: fixed 512; no paste-back | [41] |
| SkyReels-A1 (CogVideoX-5B) | Driving video (3D landmarks) or audio | Whole frame, 480x720 class | Not documented | Skywork Community License | Not published | Official repo, Python 3.10 | Not picked: pytorch3d and insightface 0.7.3 need a compiler | [42] |
| X-NeMo (SVD plus sd-image-variations) | Driving video | Face crop | Not documented | Weights CC BY-NC 4.0, academic research only | 24 GB | Official repo, Python 3.9, Google Drive weights | Not picked: crop only | [43] |
| X-Portrait (SD 1.5) | Driving video | 512x512 crop | Not documented | Apache-2.0 | Not published | Official repo, Python 3.9, CUDA 11.8 | Not picked: old pins; crop only | [44] |
| Follow-Your-Emoji (SD 1.5 plus AnimateDiff) | Landmark `.npy`; one template bundled | 512x512 crop | Not documented | Not stated | 24 GB card used | Official repo; torch 2.0.1 pin | Not picked: worst FID and FVD in FantasyPortrait's table | [13][45] |
| AniPortrait (SD 1.5) | Driving video, pose or audio | Face and head, 512x512 | Not documented | Apache-2.0 | Not published | Official repo, CUDA 11.7 | Not picked: weaker in every table that includes it | [46] |
| MegActor-Sigma (SD 1.5) | Driving video or audio | Face and head | Not documented | Apache-2.0 | Not published | Official repo, conda env | Not picked: identity 0.606 in PersonaLive's table | [40][47] |
| MOFA-Video (SVD adapters) | Trajectories plus facial landmarks | Whole image | Not documented | Apache-2.0 except third-party parts | Not published | Official Gradio demo | Not picked: pytorch3d needs a compiler | [48] |
| Cinemo (LaVie) | Text plus motion intensity 0 to 19 | Whole image, fixed 320x512 | Not applicable | Apache-2.0 | Not published | Official repo, conda env | Not picked: no face identity mechanism | [49] |
| PIA (SD 1.5 plug-in) | Text plus motion magnitude 0, 1 or 2 | Whole image, up to 1024x1024 | Not applicable | Apache-2.0 | 16 GB at 1024x1024 | Official repo | Not picked: no face identity mechanism | [50] |
| Motion-I2V (SD 1.5 plus AnimateDiff) | Text, motion brush, drag trajectories | Whole image or brushed region, 320x512 | Not applicable | Not stated | Not published | Official repo, conda env | Not picked: low resolution; no face identity mechanism | [51] |
| AnimateAnything (SVD variant) | Mask, text and motion strength | Whole image or masked region | Not applicable | MIT | Not published | Official repo, Python 3.10 | Not picked: no face identity mechanism | [52] |
| X-Dyna (SD 1.5 plus ControlNets) | Body pose plus face expression from a driving video | Whole body, hair and background, 896x512 | Not documented | Apache-2.0 code; README says research only | 20 GB for 16 frames | Official repo, torch 2.0.1+cu118 | Not picked: body-pose driving; research only | [53] |
| MimicMotion (SVD 1.1) | Pose sequence | Whole body, 576x1024 | Not documented | Apache-2.0; SVD community licence | 16 GB for 72 frames | Official repo | Not picked: body-pose driving | [54] |
| StableAnimator (SVD) | Pose sequence | Whole body with a face ID adapter | Not documented | MIT | 8 GB, basic model | Official repo, torch 2.5.1 cu124 | Not picked: body-pose driving | [55] |

## 4. Excluded models

This section lists the models left out and the reason for each.

| Model or group | Reason | Sources |
|---|---|---|
| General-purpose image-to-video models (Wan, HunyuanVideo, LTX-Video, CogVideoX, SkyReels-V, Step-Video, MAGI-1, FramePack, Kandinsky video and similar) | Out of scope by the Star Colonel's decision; not researched or ranked | - |
| Wan-Animate (Wan2.2-Animate-14B, base Wan2.2-I2V-A14B) | The model card publishes it as "an unified model for character animation and replacement", not as portrait or photo animation, so it is out under the 2026-10-24 ruling as written. It also has the lowest identity among the baselines in PerformRecast's editing table (CSIM 0.614 and 0.6062) | [26][57] |
| Wan-Animate-2, SteadyDancer, MultiAnimate, One-to-All Animation | Wan fine-tunes for pose-driven character or whole-body animation, the same class as Wan-Animate (medium) | [58][59] |
| LivePhoto-Wan2.1 | LoRA plus base weights on Wan2.1-T2V-1.3B; out by the ruling on LoRAs and adapters. The original SD 1.5 LivePhoto has no weights in the repository | [61] |
| EditaLive | Three LoRAs on Wan2.2-Animate-14B for character video editing; weights released 2026-09-14; academic research only | [60] |
| Viggle-Animate | Replaces a character inside a driving video; MiniMax H3 Community License; needs 96 GB or offload | [62] |
| Ditto | Audio-driven; inference requires `--audio_path`; no silent or idle mode documented | [63] |
| Hallo2, Hallo3, EchoMimic V1 to V3, HunyuanVideo-Avatar, GoHD, InfiniteTalk, MultiTalk, SkyReels-A3 | Audio-driven talking heads with no documented silent idle mode | [64] |
| SoulX-FlashTalk, EchoMimicV3-Flash, SoulX-FlashHead, LiveAvatar | Audio-driven avatars of 2025-12 to 2026-02; the one test found says nothing about silent behaviour (medium) | [38] |
| Durian, ExpPortrait, DeX-Portrait, HairWeaver, IMTalker, Loki, CogPortrait, Avatar V, FactorPortrait, Stable Video-Driven Portraits, DreamLoop, MiraMo, Follow-Your-Emoji-Faster, Follow-Your-Click, Automatic Animation of Hair Blowing, CycleNet | No released code or weights found | [65] |
| StyleCineGAN, Text2Cinemagraph, OuroWorld, LiveMoments, Immersity AI | Do not animate a still photo of a person, or are a closed service | [66] |
| FasterLivePortrait (a LivePortrait runtime) | Needs TensorRT 8.x, which does not support Blackwell | [11] |

## 5. Test plan

This section gives the recipe for each model and the run for each test photo. The measured results come from a later test run. The machine-readable recipes are in `tmp/workflows/live-photo-research/final-shortlist.json`.

### 5.1 Shared preparation

These steps apply to every model.

1. Make 720x960 Lanczos copies of the three photos for FantasyPortrait and FlashPortrait. All three photos are within 0.4 % of 3:4. LivePortrait and PerformRecast use the original files
2. Set `CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=<nvidia-smi index>` before torch is imported. CUDA's default order is fastest first, so without `PCI_BUS_ID` an index can point at a different card [24]
3. After the downloads, run every model with `HF_HUB_OFFLINE=1`, and run `yolo settings sync=False` once in the ComfyUI venv. With `sync` on and the host online, ultralytics sends usage events (versions, hardware, timings, no image content) to Google Analytics [8]
4. Run LivePortrait first on GPU 2. It produces 77-frame 25 fps clips: one per photo, plus one per child for photo (b). These are the driving videos for all other models
5. Run FantasyPortrait on GPU 1 and FlashPortrait on GPU 2 at the same time
6. Judge each clip against the bar: face identity at 100 % zoom against the photo, no seam at the mask edge, motion limited to a blink, a small smile or turn and a little hair movement, length about 3 s

### 5.2 LivePortrait test

LivePortrait runs in ComfyUI with the AdvancedLivePortrait node, which generates the motion from two edited expressions.

- **Files** - five safetensors from `Kijai/LivePortrait_safetensors` (0.52 GB) into `ComfyUI/models/liveportrait/`, and `face_yolov8n.pt` (6.2 MB) from `Bingsu/adetailer` into `ComfyUI/models/ultralytics/` [5]. The node downloads only missing files [3]
- **Environment** - ComfyUI in its own uv venv, Python 3.13. torch and torchvision come from the cu130 index, which the ComfyUI README requires on Nvidia 20 series and newer [6]. `nvidia-smi` must report CUDA 13.0 or newer; otherwise update the Windows driver
- **Nodes** - ComfyUI-AdvancedLivePortrait with its requirements, including `rich>=13.7.1`, `tyro==0.8.5` and `lmdb>=1.4.1`, which has a cp313 wheel [3][9]. ComfyUI-VideoHelperSuite uses the imageio-ffmpeg binary when ffmpeg is not on PATH [7]
- **torch.compile** - leave it off. Triton raises "Failed to find C compiler" on a host with no compiler [10]
- **Issue #89** - a weights-only error when loading `face_yolov8n.pt` on torch 2.6 or newer is reported, with an unmerged patch [4]. Current ultralytics loads checkpoints with `weights_only=False` [8], so patch `nodes.py` only if the error appears
- **Editor 1** - `smile` 0.2, `rotate_yaw` 3, `rotate_pitch` -1, other sliders 0, `crop_factor` 1.7
- **Editor 2** - `motion_link` from editor 1, with the same values plus `blink` -18. Each editor builds its expression only from its own sliders, so editor 2 with blink alone would turn the head back to 0 and out again within 6 frames [3]
- **Command** - `animate_without_vid` True, `crop_factor` 1.7, `retargeting_eyes` 0, `retargeting_mouth` 0, and the lines `0=1:14`, `1=15:10`, `2=3:2`, `1=3:29`. That gives 15 frames of the photo's own expression, 25 frames into the smile and turn, 5 frames of blink and 32 frames reopening: 77 frames at 25 fps, 3.08 s
- **Output** - Video Combine at 25 fps, `video/h264-mp4`, plus PNG frames for photo (b)
- **Values** - a starting proposal (low). Check on editor 2's image output that a negative blink closes the eyes. If the motion is too strong, halve `smile` and `rotate_yaw` in both editors
- **Fallback** - the official CLI is already cloned with its weights at `models/photo-animation/LivePortrait/` on the project `.venv` (`models/photo-animation.md`, no run result recorded). Drive it with `wink.pkl`, `--driving_multiplier 0.5 --animation_region exp --source_max_dim 2000` [2]
- **GPU and time** - GPU 2. No VRAM figure is published; about 4 GB is expected (low). Under 1 minute per clip is expected (low), from 12.8 ms per frame on an RTX 4090 [1]

| Photo | Run | What moves | Check |
|---|---|---|---|
| (a) 1034x1374 | Original file, settings above | Face and the hair inside the 1.7x crop | Softness and seam at the face edge, frame 1 against the photo at 100 % |
| (b) 962x1278 | One rectangle per child, each holding the 1.7x crop with a margin and excluding the neighbours' faces where possible. Commands: left `0=1:6`, `1=15:10`, `2=3:2`, `1=3:37`; middle as above; right `0=1:24`, `1=15:10`, `2=3:2`, `1=3:19`. Composite the PNG frames as frame_t = photo + sum over k of (rect_k_frame_t - rect_k_photo) | Three faces, blinking at different times | Without rectangles the node animates only the face nearest the horizontal centre [3]. The rectangle method is an untested proposal |
| (c) 1500x2000 | Both editors with `smile` 0.15 and no rotation; editor 2 adds `blink` -18 | Face only; curls outside the crop stay still | Editor 1's image output shows the face. If YOLO finds no face (confidence 0.7, width 30 px), the node uses the whole image and the result fails [3] |

### 5.3 FantasyPortrait test

FantasyPortrait runs from its official repository with the LivePortrait clips as driving videos.

- **Files** - from `acvlab/FantasyPortrait`: `fantasyportrait_model.ckpt` (4.01 GB), `pd_fpg.pth` (0.04 GB), `face_det.onnx` and `face_landmark.onnx`. The whole `Wan-AI/Wan2.1-I2V-14B-720P` repository adds 82.2 GB, for 86.3 GB in total [16]
- **Environment** - own uv venv, Python 3.12, torch and torchvision 2.7 or newer from the cu128 index [23], and `requirements.txt` as it is [14]. `cupy-cuda12x` 14.2.0 installs from a prebuilt wheel [17]
- **Added packages** - `onnx` and `onnxruntime-gpu==1.22.0`, which `face_utils.py` imports but `requirements.txt` does not list [14]. onnxruntime-gpu 1.23.0 and 1.23.1 fail on RTX 5090 [18]. Add `moviepy` 2.x, which `infer_multi.py` imports [14]
- **flash-attn** - do not install it. The DiT falls back to torch SDPA [14]. In issue #9, flash-attn compiled and then failed to import with an undefined C++ symbol [15]
- **ffmpeg** - link `.venv/bin/ffmpeg` to the imageio-ffmpeg binary and put `.venv/bin` first on PATH. `infer.py` ends with an ffmpeg call that has no error handling, so without ffmpeg every run exits with an error after the silent mp4 is written [14]
- **pd_fpg.pth** - `torch.load` is called without `weights_only` [14]. If loading fails, `weights_only=False` runs pickle code from the official file; decide before applying it

```bash
CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=1 HF_HUB_OFFLINE=1 PATH="$PWD/.venv/bin:$PATH" \
python infer.py \
  --wan_model_path models/Wan2.1-I2V-14B-720P \
  --portrait_checkpoint models/FantasyPortrait/fantasyportrait_model.ckpt \
  --pd_fpg_model_path models/FantasyPortrait/pd_fpg.pth \
  --det_model_path models/FantasyPortrait/face_det.onnx \
  --alignment_model_path models/FantasyPortrait/face_landmark.onnx \
  --input_image_path photo_a_720x960.png \
  --driven_video_path lp_a_77f.mp4 \
  --output_path out/fantasy_a \
  --prompt "" --num_frames 77 --max_size 960 \
  --cfg_scale 1.0 --portrait_scale 1.0 --portrait_cfg_scale 4.0 --seed 42
```

- **Fixed in the code** - 30 steps, bf16, the whole DiT on the GPU; fps from the driving video; frames rounded down to 4n+1, giving 77 frames, 3.08 s [14]
- **Guidance** - the values come from the repository's shell scripts. `infer.py` defaults to 5.0 for both, so pass them explicitly [14]. If the motion is too strong, run again with `--portrait_cfg_scale 3.0` (inference)
- **`--scale_image`** - never pass it. It is declared `type=bool`, so any value, including `False`, becomes True [14]
- **VRAM** - the README gives 40 GB at full load on one A100 with no resolution stated [14]. The 50-60 GB user figure in issue #5 was measured in an offload mode, so full load at 720x960 can need more [15]. Run on GPU 1 (96 GB) at full load, because the offload modes depend on pinned host memory, which WSL2 limits [25]. On out-of-memory, use 576x768 with `--max_size 768`
- **Time** - 11 to 25 minutes per clip (low), from FlashPortrait's measurement of 4339 s for a 20 s 480x832 clip [19]

| Photo | Run | What moves | Check |
|---|---|---|---|
| (a) | `infer.py` as above | Whole frame regenerated; face, hair and body can move | Face identity against the photo at the same scale; grid pattern from issue #16 [15] |
| (b) | `infer_multi.py` with the same paths, `photo_b_720x960.png` and `--driven_video_path lp_b_left.mp4 lp_b_middle.mp4 lp_b_right.mp4` | Three faces, each from its own clip | The detector must find exactly three faces; faces are sorted left to right and paired with videos by index [14]. If motions look swapped, reverse the video order (low) |
| (c) | `infer.py` with `lp_c_77f.mp4` | Whole frame; curls can move | Hair motion stays small; face unchanged |

### 5.4 FlashPortrait test

FlashPortrait runs from its official `fast_infer.py` with the 4-step distillation LoRA and the shared Wan2.1 folder.

- **Files** - from `FrancisRing/FlashPortrait`: `transformer.pt` (57.12 GB), `fast_lora_rank64.safetensors` (0.74 GB), `portrait_encoder.pt` (0.33 GB), `pd_fpg.pth`, `fast_vae.pth`, `face_det.onnx` and `face_landmark.onnx`, 58.3 GB in total [21]. The script loads the base DiT, T5, CLIP and VAE from the Wan2.1 folder of test 2 and applies `transformer.pt` on top [20]
- **Environment** - own uv venv, Python 3.12, because `numpy<2` has no cp313 wheel [22]. torch and torchvision 2.7 or newer from the cu128 index; the README's torch 2.6.0 cu124 has no sm_120 kernels [20][23]
- **Packages** - `requirements.txt` without `deepspeed`, with `onnxruntime-gpu==1.22.0`, plus `xfuser`, which `fast_infer.py` imports but `requirements.txt` does not list [20]. xfuser 0.7.0 requires `diffusers>=0.33.0`; whether FlashPortrait runs with it is not verified (medium) [22]
- **Settings in `fast_infer.py`** - the ten path variables, `max_size = 960`, `GPU_memory_mode = "model_full_load"`, `weight_dtype = torch.bfloat16`, `enable_step_distill = True` (steps 1000, 750, 500, 250), `emo_cfg_scale = 4.0`, `text_cfg_scale = 1.0`, `seed = 42` [20]
- **Prompt** - replace the default "The girl is singing" with a neutral description such as "A young child sits still with a calm, natural expression" (proposal)
- **Tiny VAE** - `wan_fast.yaml` turns it on [20]. Turn it off for the identity test (inference)
- **Frames** - 77 from the driving clip; the saved video drops the first frame, leaving 76 frames at 25 fps, 3.04 s [20]
- **pd_fpg.pth** - same `weights_only` decision as in test 2 [20]
- **Launch** - `CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=2 HF_HUB_OFFLINE=1 python fast_infer.py`
- **VRAM and time** - the README gives about 60 GB at full load for 10 s at 720x1280 [20]; 45-60 GB is expected for 3 s at 720x960 (inference). On out-of-memory, move to GPU 1. 2 to 5 minutes per clip is expected (low), from 720 s for a 20 s 480x832 clip [19], plus the time to load about 140 GB of weights

| Photo | Run | What moves | Check |
|---|---|---|---|
| (a) | 720x960 copy, `lp_a_77f.mp4` | Whole frame regenerated | Face identity. 720x960 is not in the README's size list; if artefacts appear, pad to 720x1280 with 160 edge rows at top and bottom, `max_size = 1280`, and crop rows 160 to 1119 [20] |
| (b) | Diagnostic only, with the middle child's clip | One face driven, two uncontrolled | Not supported: the face aligner returns one face per frame, and its largest-face loop has a bug [20] |
| (c) | 720x960 copy, `lp_c_77f.mp4` | Whole frame; curls can move | Same checks as (a) |

### 5.5 PerformRecast reserve

PerformRecast runs from its official `inference.py` only if LivePortrait shows a seam.

- **Files** - `scripts/download_weights.sh` downloads seven artefacts from Google Drive into `pretrained_weights/`: the four PerformRecast networks, a DINO ViT-B/16, InsightFace `buffalo_l` and `landmark.onnx` [28]. No sizes are published; about 1.2 GB is expected (low)
- **Environment** - own uv venv, Python 3.12, `torch==2.11.0` and `torchvision==0.26.0` from the cu128 index [28], and `requirements.txt` with `onnxruntime-gpu` pinned to 1.22.0 [18]
- **ffmpeg** - both `ffmpeg` and `ffprobe` must be on PATH. Install `static-ffmpeg` or place a static build in `./ffmpeg/` at the repository root [12][28]
- **Input** - the released pipeline reads the source as a video [28]. Encode each photo as a static 77-frame 25 fps lossless video, for example `ffmpeg -loop 1 -framerate 25 -i photo_a.png -frames:v 77 -c:v libx264rgb -crf 0 photo_a_static77.mp4` (proposal)
- **Command** - `CUDA_DEVICE_ORDER=PCI_BUS_ID CUDA_VISIBLE_DEVICES=0 HF_HUB_OFFLINE=1 python3 inference.py -s photo_a_static77.mp4 -d lp_a_77f.mp4 -o out/performrecast_a --inference-mode 1 --device-id 0`. Mode 1 is replacement, the README's recommended default. Turn off `--flag-use-half-precision` if frames come out black [28]
- **Output** - `*.mp4` pasted back at the source resolution; output fps from the source; frames = the shorter of the two inputs [28]
- **GPU and time** - GPU 0. No VRAM or time figure is published; about 4 GB and under 1 minute per clip are expected for a LivePortrait-class network (low)

| Photo | Run | What moves | Check |
|---|---|---|---|
| (a) | Static video of the original photo, `lp_a_77f.mp4` | Expression only; no head turn | Seam at the face edge against test 1 |
| (b) | Three runs with `face_index` 0, 1 and 2 (check the flag spelling with `--help`); composite the PNG frames as in test 1 | Three faces, expression only | The face order is not documented; faces under about 80 px may not be detected [28] |
| (c) | As (a), with the 1500x2000 photo | Face only; curls stay still | Detection if the child looks down |

### 5.6 HunyuanPortrait reserve

HunyuanPortrait runs from its official `inference.py` only after the Star Colonel accepts its licence.

- **Files** - `tencent/HunyuanPortrait` (7.34 GB), the configs and fp16 VAE of `stabilityai/stable-video-diffusion-img2vid-xt`, `yoloface_v5m.pt` from `LeonJoe13/Sonic` and `arcface.onnx` from `FoivosPar/Arc2Face` [30][32]
- **Environment** - own uv venv, Python 3.12, cu128 torch. Install the requirements without `onnxruntime` and with `onnxruntime-gpu` pinned to 1.22.0; `diffusers==0.29.0` and `moviepy==1.0.1` are pinned [30]. decord 0.6.0 has a prebuilt wheel [33]
- **ArcFace** - the session uses the CUDA provider only, with no CPU fallback, so a CUDA provider failure stops the run [30]
- **Settings** - the config gives 512x512, 25 steps, 25-frame windows with an overlap of 3, and fp16 [30]. Keep `full_resolution.mp4`, which pastes the generated square back with a soft mask; both outputs are written at the driving video's fps [30]
- **GPU and time** - GPU 2. Under 20 GB for 4 s on an RTX 3090 [31]. About 4 minutes per clip is expected (low), from 1602 s for a 20 s 480x832 clip [19]
- **Licence** - `LICENSE` and `LICENSE_MODEL` limit use to academic, research and education purposes and forbid commercial or production use [30]. A third-party ComfyUI node exists but has been inactive since 2025-05-28 [34]

| Photo | Run | What moves | Check |
|---|---|---|---|
| (a) | `inference.py` with `lp_a_77f.mp4` | 512x512 head-and-shoulders square, pasted back | Blend boundary of the square; identity |
| (b) | Not run | One face only | - |
| (c) | Not run | Head and shoulders only; curls outside the square stay still | - |

## 6. Caveats and confidence

This section states how far each part of this document can be trusted.

| Statement | Confidence | Basis |
|---|---|---|
| Order of the three test models | Medium | Scored assessment from cited facts; no test on a child's face |
| Files, sizes, arguments and package facts | High | Code, file trees and READMEs read on 2026-10-24 and checked by a fact verifier |
| Expression values, rectangle compositing, static-video input, motion-strength levers | Low | Proposals, untested |
| VRAM and time per clip | Low | Measured on other GPUs; linear extrapolation to 3 s |
| PerformRecast table values | Medium | Extracted by an automated reader; the order is reliable, single values need a spot-check |
| Wan-Animate out of scope | High for the model card text | The Star Colonel can rule otherwise |
| No other purpose-built release in 2026 | Medium | Web searches and project pages on 2026-10-24 |

- No paper, benchmark or community test covers children's faces. The local test is the only identity evidence that will apply
- No published Blackwell run produced a frame for any of the three test models. The only Blackwell report, for FantasyPortrait, ran out of memory while loading on a 32 GB RTX 5090 [15]
- Driving the diffusion models with LivePortrait clips is untested, and a diffusion model can add motion of its own
- Every diffusion output is smaller than the photo: 720x960 for the Wan2.1 models and a 512x512 square for HunyuanPortrait
- ComfyUI needs a cu130 torch, so the Windows driver must support CUDA 13.0
- The HunyuanPortrait licence decision is open

## 7. Sources

1. LivePortrait paper - https://arxiv.org/html/2407.03168
2. LivePortrait repository, LICENSE, argument_config.py, cropper.py and weights record - https://github.com/KwaiVGI/LivePortrait , https://raw.githubusercontent.com/KwaiVGI/LivePortrait/main/LICENSE , https://raw.githubusercontent.com/KwaiVGI/LivePortrait/main/src/config/argument_config.py , https://raw.githubusercontent.com/KwaiVGI/LivePortrait/main/src/utils/cropper.py , https://huggingface.co/api/models/KwaiVGI/LivePortrait
3. ComfyUI-AdvancedLivePortrait repository, nodes.py and requirements.txt - https://github.com/PowerHouseMan/ComfyUI-AdvancedLivePortrait , https://raw.githubusercontent.com/PowerHouseMan/ComfyUI-AdvancedLivePortrait/main/nodes.py , https://raw.githubusercontent.com/PowerHouseMan/ComfyUI-AdvancedLivePortrait/main/requirements.txt
4. ComfyUI-AdvancedLivePortrait issue #89 - https://github.com/PowerHouseMan/ComfyUI-AdvancedLivePortrait/issues/89
5. Kijai/LivePortrait_safetensors and Bingsu/adetailer file trees - https://huggingface.co/api/models/Kijai/LivePortrait_safetensors/tree/main , https://huggingface.co/api/models/Bingsu/adetailer/tree/main
6. ComfyUI README - https://raw.githubusercontent.com/comfyanonymous/ComfyUI/master/README.md
7. ComfyUI-VideoHelperSuite utils.py - https://raw.githubusercontent.com/Kosinkadink/ComfyUI-VideoHelperSuite/main/videohelpersuite/utils.py
8. ultralytics patches.py and events.py - https://raw.githubusercontent.com/ultralytics/ultralytics/main/ultralytics/utils/patches.py , https://raw.githubusercontent.com/ultralytics/ultralytics/main/ultralytics/utils/events.py
9. PyPI lmdb 3.0.0 - https://pypi.org/pypi/lmdb/3.0.0/json
10. Triton build.py - https://raw.githubusercontent.com/triton-lang/triton/main/python/triton/runtime/build.py
11. FasterLivePortrait README - https://github.com/warmshao/FasterLivePortrait
12. PyPI static-ffmpeg - https://pypi.org/pypi/static-ffmpeg/json
13. FantasyPortrait paper - https://arxiv.org/html/2507.12956
14. FantasyPortrait repository and code - https://github.com/Fantasy-AMAP/fantasy-portrait , https://raw.githubusercontent.com/Fantasy-AMAP/fantasy-portrait/main/requirements.txt , https://raw.githubusercontent.com/Fantasy-AMAP/fantasy-portrait/main/infer.py , https://raw.githubusercontent.com/Fantasy-AMAP/fantasy-portrait/main/infer_multi.py , https://raw.githubusercontent.com/Fantasy-AMAP/fantasy-portrait/main/infer_multi_diff.sh , https://raw.githubusercontent.com/Fantasy-AMAP/fantasy-portrait/main/diffsynth/models/face_utils.py , https://raw.githubusercontent.com/Fantasy-AMAP/fantasy-portrait/main/diffsynth/models/wan_video_dit.py
15. FantasyPortrait issues #5, #9 and #16 - https://github.com/Fantasy-AMAP/fantasy-portrait/issues/5 , https://github.com/Fantasy-AMAP/fantasy-portrait/issues/9 , https://github.com/Fantasy-AMAP/fantasy-portrait/issues/16
16. acvlab/FantasyPortrait and Wan2.1-I2V-14B-720P file trees - https://huggingface.co/api/models/acvlab/FantasyPortrait/tree/main , https://huggingface.co/api/models/Wan-AI/Wan2.1-I2V-14B-720P/tree/main
17. PyPI cupy-cuda12x 14.2.0 and onnxruntime-gpu 1.22.0 - https://pypi.org/pypi/cupy-cuda12x/14.2.0/json , https://pypi.org/pypi/onnxruntime-gpu/1.22.0/json
18. onnxruntime PR #26230 (Blackwell build targets) - https://github.com/microsoft/onnxruntime/pull/26230
19. FlashPortrait paper - https://arxiv.org/html/2512.16900v1
20. FlashPortrait repository and code - https://github.com/Francis-Rings/FlashPortrait , https://raw.githubusercontent.com/Francis-Rings/FlashPortrait/main/requirements.txt , https://raw.githubusercontent.com/Francis-Rings/FlashPortrait/main/fast_infer.py , https://raw.githubusercontent.com/Francis-Rings/FlashPortrait/main/config/wan2.1/wan_fast.yaml , https://raw.githubusercontent.com/Francis-Rings/FlashPortrait/main/wan/models/face_align.py
21. FrancisRing/FlashPortrait file tree - https://huggingface.co/api/models/FrancisRing/FlashPortrait/tree/main
22. PyPI xfuser, yunchang, distvae and numpy 1.26.4 - https://pypi.org/pypi/xfuser/json , https://pypi.org/pypi/yunchang/json , https://pypi.org/pypi/distvae/json , https://pypi.org/pypi/numpy/1.26.4/json
23. PyTorch 2.7 release blog - https://pytorch.org/blog/pytorch-2-7/
24. NVIDIA CUDA environment variables - https://docs.nvidia.com/cuda/cuda-programming-guide/05-appendices/environment-variables.html
25. NVIDIA CUDA on WSL user guide - https://docs.nvidia.com/cuda/wsl-user-guide/index.html
26. PerformRecast paper (identity tables) - https://arxiv.org/html/2603.19731
27. PerformRecast project page - https://youku-aigc.github.io/PerformRecast
28. PerformRecast repository, requirements.txt and pipeline.py - https://github.com/youku-aigc/PerformRecast , https://raw.githubusercontent.com/youku-aigc/PerformRecast/main/requirements.txt , https://raw.githubusercontent.com/youku-aigc/PerformRecast/main/src/pipeline.py
29. HunyuanPortrait paper - https://arxiv.org/html/2503.18860v2
30. HunyuanPortrait repository and files - https://github.com/Tencent-Hunyuan/HunyuanPortrait , https://raw.githubusercontent.com/Tencent-Hunyuan/HunyuanPortrait/main/LICENSE , https://raw.githubusercontent.com/Tencent-Hunyuan/HunyuanPortrait/main/LICENSE_MODEL , https://raw.githubusercontent.com/Tencent-Hunyuan/HunyuanPortrait/main/requirements.txt , https://raw.githubusercontent.com/Tencent-Hunyuan/HunyuanPortrait/main/config/hunyuan-portrait.yaml , https://github.com/Tencent-Hunyuan/HunyuanPortrait/blob/main/inference.py
31. HunyuanPortrait issue #4 (VRAM) - https://github.com/Tencent-Hunyuan/HunyuanPortrait/issues/4
32. tencent/HunyuanPortrait file tree and SVD img2vid-xt record - https://huggingface.co/api/models/tencent/HunyuanPortrait/tree/main , https://huggingface.co/api/models/stabilityai/stable-video-diffusion-img2vid-xt
33. PyPI decord 0.6.0 - https://pypi.org/pypi/decord/0.6.0/json
34. ComfyUI-HunyuanPortrait, third party - https://api.github.com/repos/Yuan-ManX/ComfyUI-HunyuanPortrait
35. LongCat-Video repository and attention.py - https://github.com/meituan-longcat/LongCat-Video , https://github.com/meituan-longcat/LongCat-Video/blob/main/longcat_video/modules/attention.py
36. LongCat-Video-Avatar 1.5 technical report - https://arxiv.org/html/2605.26486
37. LongCat-Video-Avatar-1.5 model card and repository sizes - https://huggingface.co/meituan-longcat/LongCat-Video-Avatar-1.5 , https://huggingface.co/api/models/meituan-longcat/LongCat-Video-Avatar-1.5/treesize/main , https://huggingface.co/api/models/meituan-longcat/LongCat-Video/treesize/main
38. Tight Studio test of open-source avatar models (August 2026) - https://tight.studio/blog/open-source-talking-avatar-models/
39. SadTalker repository and gradio_demo.py - https://github.com/OpenTalker/SadTalker , https://raw.githubusercontent.com/OpenTalker/SadTalker/main/src/gradio_demo.py
40. PersonaLive repository and paper - https://github.com/GVCLab/PersonaLive , https://arxiv.org/html/2512.11253
41. LIA-X repository and paper - https://github.com/wyhsirius/LIA-X , https://arxiv.org/html/2508.09959v1
42. SkyReels-A1 repository, paper and requirements.txt - https://github.com/SkyworkAI/SkyReels-A1 , https://arxiv.org/html/2502.10841 , https://raw.githubusercontent.com/SkyworkAI/SkyReels-A1/main/requirements.txt
43. X-NeMo inference repository and paper - https://github.com/bytedance/x-nemo-inference , https://arxiv.org/html/2507.23143
44. X-Portrait repository - https://github.com/bytedance/X-Portrait
45. Follow-Your-Emoji repository - https://github.com/mayuelala/FollowYourEmoji
46. AniPortrait repository - https://github.com/Zejun-Yang/AniPortrait
47. MegActor repository - https://github.com/megvii-research/MegActor
48. MOFA-Video repository and PyPI pytorch3d - https://github.com/MyNiuuu/MOFA-Video , https://pypi.org/pypi/pytorch3d/json
49. Cinemo repository - https://github.com/maxin-cn/Cinemo
50. PIA repository - https://github.com/open-mmlab/PIA
51. Motion-I2V repository - https://github.com/G-U-N/Motion-I2V
52. AnimateAnything repository - https://github.com/alibaba/animate-anything
53. X-Dyna repository - https://github.com/bytedance/X-Dyna
54. MimicMotion repository - https://github.com/Tencent/MimicMotion
55. StableAnimator repository - https://github.com/Francis-Rings/StableAnimator
56. ExpPortrait and DeX-Portrait papers (identity tables) - https://arxiv.org/html/2602.19900 , https://arxiv.org/html/2512.15524
57. Wan2.2-Animate-14B model card and ComfyUI tutorial - https://huggingface.co/Wan-AI/Wan2.2-Animate-14B , https://docs.comfy.org/tutorials/video/wan/wan2-2-animate
58. Wan-Animate-2 repository - https://github.com/Wan-Video/Wan-Animate-2
59. SteadyDancer, MultiAnimate and One-to-All Animation repositories - https://github.com/MCG-NJU/SteadyDancer , https://github.com/hyc001/MultiAnimate , https://github.com/ssj9596/One-to-All-Animation
60. EditaLive repository - https://github.com/GVCLab/EditaLive
61. LivePhoto repository - https://github.com/XavierCHEN34/LivePhoto
62. Viggle-Animate model card - https://huggingface.co/Viggle/Viggle-Animate
63. Ditto repository - https://github.com/antgroup/ditto-talkinghead
64. Audio-driven models with no documented silent mode - https://arxiv.org/pdf/2410.07718 , https://github.com/fudan-generative-vision/hallo3 , https://github.com/antgroup/echomimic , https://huggingface.co/BadToBest/EchoMimicV3 , https://arxiv.org/pdf/2505.20156 , https://github.com/jia1018/GoHD , https://www.runcomfy.com/models/community/infinite-talk/fast/multi , https://finance.sina.cn/2025-08-11/detail-infkqmzi9886253.d.html?vt=4
65. Models with no released code or weights - https://github.com/snuvclab/durian , https://ustc3dv.github.io/ExpPortrait/ , https://syx132.github.io/DeX-Portrait/ , https://boese0601.github.io/hairweaver/ , https://arxiv.org/html/2511.22167v1 , https://arxiv.org/abs/2605.24176 , https://arxiv.org/abs/2605.28056 , https://arxiv.org/abs/2606.13872 , https://arxiv.org/html/2512.11645v1 , https://arxiv.org/abs/2509.17476v1 , https://arxiv.org/abs/2601.02646 , https://github.com/maxin-cn/MiraMo , https://arxiv.org/abs/2509.16630 , https://github.com/mayuelala/FollowYourClick , https://nevergiveu.github.io/AutomaticHairBlowing/ , https://research.adobe.com/publication/blowing-in-the-wind-cyclenet-for-human-cinemagraphs-from-still-images
66. Models that do not animate a still photo of a person - https://openaccess.thecvf.com/content/CVPR2024/html/Choi_StyleCineGAN_Landscape_Cinemagraph_Generation_using_a_Pre-trained_StyleGAN_CVPR_2024_paper.html , https://api.crossref.org/works/10.1145%2F3618326 , https://arxiv.org/html/2610.12461v1 , https://www.alphaxiv.org/abs/2604.12286.md

<!-- complete -->
