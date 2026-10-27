# Henryk Media - Image extender model selection v1

Status: DECISION RECORD for notebook 01, 2026-10-25. The machine-readable decision is `tmp/workflows/image-extender/choice.json`. This revision uses the outpaint, upscale and local checkpoints written at 03:19 to 03:21.

## Contents

- [1. Use case and bar](#1-use-case-and-bar)
- [2. Recommendation](#2-recommendation)
  - [2.1 Outpainting choice](#21-outpainting-choice)
  - [2.2 Upscaling choice](#22-upscaling-choice)
  - [2.3 One pass or two](#23-one-pass-or-two)
  - [2.4 Decision rule](#24-decision-rule)
- [3. Candidate comparison](#3-candidate-comparison)
  - [3.1 Outpainting](#31-outpainting)
  - [3.2 Upscaling](#32-upscaling)
- [4. Excluded candidates](#4-excluded-candidates)
- [5. Licensing facts](#5-licensing-facts)
- [6. Pipeline the notebook runs](#6-pipeline-the-notebook-runs)
- [7. Caveats and confidence](#7-caveats-and-confidence)
- [8. Sources](#8-sources)

## 1. Use case and bar

The extender takes one portrait photo of Henry and returns a 4:3 landscape image at a higher resolution, so the whole-frame image-to-video model (LTX-2.5) animates a finished frame and invents no scene. The first source photo is `data/interim/henryk-urodziny-2026/IMG_8564.png`, 962x1278 px, ratio 0.7527 [38]. The LTX-2.5 graph takes width and height as multiples of 32 [37].

| Quantity | Value | Basis |
|---|---:|---|
| Source | 962x1278 | [38] |
| 4:3 at the photo's native height | 1704x1278 | 4/3 x 1278 = 1704 |
| New pixels per side | 371 | (1704 - 962) / 2 |
| New area of the final frame | 43.5% | 742 / 1704 |
| Production target | 2048x1536 | 4:3, 3.15 MP, both sides multiples of 32 [37] |
| Scale from extended to production | 1.2x each side | 2048 / 1704 = 1536 / 1278 |
| Bench upscale | 2x to 3408x2556 | notebook 01 compares every upscaler at 2x |

The hard bar:

- Every model runs locally; no photo of the child leaves the workstation.
- The weights are open and downloadable, and the repository, files and sizes are recorded.
- The child and every other person keep their face, expression and body.
- The added sides continue the same floor, wall, background and light.
- The model fits the 96 GB RTX PRO 6000 (nvidia-smi index 1) or the 72 GB RTX PRO 5000 (index 2) [35].
- The licence permits private, non-commercial home use. A non-commercial licence is acceptable and is recorded.
- Bench output goes under `tmp/media/`; only a production run writes into `data/`.

The extension is large: 43.5% of the final frame is new scene. That fact selects the workflow more than any benchmark rank does. A mask-based model keeps the photo out of the generated area, and a composite of the original pixels back over the result makes the face rule independent of the model's behaviour.

## 2. Recommendation

The bench selected `flux3-klein` as the extender the production run uses; the research tables below predate the bench. The bench still compares every viable extender. The selection is recorded in `tmp/workflows/image-extender/choice.json` (JSON) and this document (Markdown), with each chosen tile as a `.png` and its `.md` sidecar under `tmp/media/extended/<aspect>/flux3-klein/`.

| Role | Model | Licence | Download | VRAM estimate | GPU |
|---|---|---|---:|---:|---|
| Extend | FLUX.1 Fill dev | FLUX.1 [dev] Non-Commercial v1.1.1 | 34.17 GB | about 30 GB at 1704x1278, bf16 | 1 |
| Raise | SeedVR2 3B fp16 | Apache-2.0 | 7.29 GB | about 12-18 GB at 2048x1536 | 1 |
| Alternative extend | Qwen-Image-ControlNet-Inpainting | Apache-2.0 | 61.93 GB, already on disk | about 50-60 GB at 1704x1278, bf16 | 1 |
| Alternative raise | HYPIR | Proprietary non-commercial | 6.33 GB, already on disk | about 8-12 GB at 2048x1536 | 1 |

The VRAM figures are estimates from published measurements, not measurements on this workstation [1][7][23][24][35].

### 2.1 Outpainting choice

FLUX.1 Fill dev is a 12B rectified-flow model that fills only the area selected by a mask [1]. The mask covers the two new side panels, so the photo itself is never inside the edited area, and the original pixels are composited back after decode [1][12].

- It is the strongest dedicated outpainter in this research and the model recommended for portrait work in the community walkthrough [1].
- It runs natively in ComfyUI with core nodes that the local 0.42.0 checkout already contains: `ImagePadForOutpaint` and `InpaintModelConditioning` [1][35][36].
- The chosen download is 34.17 GB: `flux1-fill-dev.safetensors` 23,804,922,408 B, `ae.safetensors` 335,304,388 B, `clip_l.safetensors` 246,144,152 B and `t5xxl_fp16.safetensors` 9,787,841,024 B [1][3].
- ComfyUI gives 12 GB minimum and 24 GB recommended VRAM, with support to 2048x2048 [1]. A 24 GB RTX 3090 outpainted a 2336x1568 image by 400 px [1]. At 1704x1278 expect about 25-35 GB peak in bf16, about 30 GB typical (estimate from those two facts) [1].
- The repository is gated. The vault token's account was refused at 02:14 and at 03:0x, then the download started at 03:20 and the 23.80 GB transformer finished by 03:25; its safetensors header and tensor extents were checked at 03:26 [35][39]. The VAE and both text encoders are not yet in the model tree and the vault was locked at the last check (03:30), so the graph cannot run yet [35][39]. The file is verified by byte size and header, and a Hub SHA-256 is added to the record when available [1][35].
- The main quality risk is the size of the extension. The new area is 43.5% of the final frame, just above the 40% at which FLUX Fill is reported weak on background replacement and large edits [1]. One pass is the default; a two-pass extension (left, then right) is the fallback [1].
- Other documented failures: visible seams and colour mismatch when strength is near 1.0, blurry, grainy, low-contrast fills in ComfyUI issue 6765, and no guarantee of pixel-perfect preservation outside the mask [1]. The community portrait walkthrough proposes guidance 8-9 and strength 0.75-0.85 as the levers [1]. The graph uses denoise 1.0, so those levers are tested on the first render.

The licence is the FLUX.1 [dev] Non-Commercial License v1.1.1 [2]. Private personal use, private entertainment and hobby projects are inside its definition of Non-Commercial Purpose, so private family use is allowed [2]. Commercial and production use need a separate BFL licence [2]. The output clauses conflict: section 2(d) says outputs may be used for any purpose including commercial, while section 4(a) forbids commercial use of data produced by the model [2]. The conflict only affects selling outputs; private use is inside the grant [2]. The full record is in section 5.

### 2.2 Upscaling choice

SeedVR2 3B fp16 is a one-step diffusion transformer trained adversarially for restoration, and it accepts a single image [23]. It is the best balance of added detail and identity retention in the ranking [23].

- It is Apache-2.0 for the weights and the code, not gated [23].
- It adds pores, eyelashes and fabric weave on a sharp photo, which is the detail gain the extender needs [23].
- The 3B is the safer starting point: the authors warn that the model can over-generate on lightly degraded inputs, and the ComfyUI node page reports that close-ups can turn skin plasticky or scaly and calls the sharp variants risky for portraits [23]. The 7B non-sharp variant is the in-family comparison, not the default [23].
- It needs no custom node. ComfyUI 0.42.0 contains `SeedVR2Preprocess`, `SeedVR2Conditioning` and `SeedVR2PostProcessing`, plus the blueprint `Upscale Video (SeedVR2 3B Int8).json` [35][36].
- The chosen download is 7.29 GB: `seedvr2_3b_fp16.safetensors` 6,784,268,336 B and `seedvr2_ema_vae_fp16.safetensors` 501,324,814 B [23]. Both files are on disk [35].
- VRAM is about 12-18 GB at 2048x1536 (estimate; the node page gives about 18 GB for 3B fp16, and a reported 512 to 2048 measurement is 14-16 GB) [23].

No upscaler has a face-identity guarantee [23][24][25]. The pipeline therefore composites the original photo rectangle back after the upscale, resampled once to the output scale. The child's pixels are not regenerated. The upscaler's detail gain applies to the new sides and the seam. This is a guard rail, not a claim that SeedVR2 cannot change a face. A full-frame SeedVR2 pass would be sharper in the face; it is adopted only if the face crop survives the comparison, because identity outranks sharpness.

### 2.3 One pass or two

No candidate does both steps well enough to use alone.

- FLUX Fill fills a mask and does not restore the detail of the photo inside the frame [1].
- SeedVR2 restores and upscales but cannot invent the missing scene [23].
- A single FLUX Fill pass at 2048x1536 is possible: pad the canvas, scale the photo to 1156x1536, fill, and composite back. The photo region would then be a plain 1.2x resample, and the fill pass would run at 3.15 MP instead of 2.18 MP. That is more compute and less detail in the photo.
- The two-step route runs the fill at the photo's native scale (1704x1278), so the photo is never pre-upscaled before outpainting, and the whole extended frame then gets a restoration pass. This is the chosen route.

### 2.4 Decision rule

- If the FLUX Fill download fails its size or SHA-256 check, or the repository refuses the token again, use Qwen-Image-ControlNet-Inpainting. It is mask-based, fully Apache-2.0, and its weights are already on disk [7][8][35].
- If the Qwen route also fails, the second alternative is FLUX.2 Klein 4B with the fal green-screen outpainting LoRA. It is Apache-2.0, 16.0 GB, and runs through the native Klein template with `LoraLoaderModelOnly`; it re-renders the canvas, so the photo composite and a green-fringe check are mandatory [16][19].
- If the added sides look weak, show a seam, or duplicate a person, run two passes (left, then right) before changing the model [1].
- If the SeedVR2 nodes fail to load or produce a black image, switch to HYPIR. Its weights and custom node are already installed and the node imported cleanly on the test server [24][35].
- If the HYPIR node cannot run without changing shared packages, use Real-ESRGAN as a resolution-only fallback and record the smaller detail gain [31][35].
- If the face crop shows a change after the upscale, the guard-rail composite is misaligned; fix the composite before changing the upscaler.

## 3. Candidate comparison

The tables rank candidates for this use: a family photo that must become 4:3 with faces unchanged and real detail added. The ranks follow the research evidence for this use, not a single benchmark leaderboard. Each row gives the evidence and the verdict.

### 3.1 Outpainting

| Rank | Model | Mechanism | Face protection | Licence | Download | VRAM at 1704x1278 | ComfyUI | Verdict | Sources |
|---|---|---|---|---|---|---:|---|---|---|
| 1 | FLUX.1 Fill dev | 12B rectified-flow mask fill | Mask on the new sides; original composited back | FLUX.1 [dev] non-commercial | 34.17 GB | about 25-35 GB bf16, estimate | Native core nodes | Chosen | [1][2][3][12] |
| 2 | FLUX.2 Klein 4B plus fal green-screen LoRA | 4B edit model plus a rank-16 outpainting LoRA | Green border outside the face; original composited back | Apache-2.0 for base and LoRA | 16.04 GB | about 20-25 GB bf16 at 2048 long edge, estimate | Native Klein template plus `LoraLoaderModelOnly` | Second alternative | [16][19] |
| 3 | Qwen-Image-ControlNet-Inpainting | 2B mask ControlNet on the 20B Qwen-Image base | True mask control; original composited back | Apache-2.0 | 61.93 GB | about 50-60 GB bf16, estimate | Native, ComfyUI 0.3.59 or newer | First alternative; weights on disk | [7][8][12][35] |
| 4 | Qwen-Image-Edit-2511 | 20B instruction editor, best Qwen identity consistency | Whole canvas re-rendered; green matte or LanPaint plus composite | Apache-2.0 | 57.70 GB | about 55-65 GB bf16, 38-42 GB fp8, estimate | Native; official Expand Image workflow | Reserve; heavy, and the source can shift | [6][7][13][20] |
| 5 | FLUX.2 Klein 9B | 9B instruction editor used for uncrop | No mask; prompt plus paste-back | FLUX non-commercial | about 34.71 GB | about 40-50 GB bf16 at 2048, estimate | Native, gated | Reserve; its own community card warns faces can shift noticeably | [16] |
| 6 | FLUX.3 Image Klein plus ausboss Outpaint LoRA | 5.6B editor plus a 0.16 GB outpainting LoRA | Grey pad plus prompt plus composite | FLUX Kommunity License v1.0 | 20.47 GB | about 45-55 GB bf16, 25-30 GB int8, estimate | Native, ComfyUI 0.41.0 or newer, gated | Reserve; trained on 0.94-1.96 MP, below the 3.15 MP target; 1 wrong result in 20 on its own card | [17] |
| 7 | Z-Image Base | 6B base model used as an inpaint model | Mask in the community workflow; original composited back | Apache-2.0 | 20.52 GB | about 25-35 GB bf16 at 2048, estimate | Native; outpainting workflow is community only | Reserve; no seam, face or quality benchmarks | [21] |
| 8 | Krea 2 Turbo plus krea2-outpaint | 12-13B edit model plus a rank-32 registered LoRA | Exact source-pixel restore plus 32 px inward feather | Krea 2 Community License, gated | 35.90 GB | about 40-50 GB bf16 at 2048x2048, estimate | Custom pipeline or unofficial node | Not chosen; best source protection, but no official ComfyUI support and wider licence obligations | [22] |
| 9 | Qwen-Image 2.1 plus ausboss Outpaint LoRA | 7B native-2K editor plus a 0.16 GB outpainting LoRA | Source anchor plus pad plus composite | Qwen Research License, research or evaluation only | 33.28 GB bf16 | about 35-45 GB bf16, 20-25 GB int8, estimate | Native | Excluded on licence | [18] |

Other in-scope candidates:

| Model | Mechanism | Licence | Download | VRAM at 1704x1278 | ComfyUI | Verdict | Sources |
|---|---|---|---|---:|---|---|---|
| FLUX.1 Kontext dev | 12B instruction editor, no mask | FLUX.1 [dev] non-commercial | 33.91 GB | about 30-35 GB bf16, estimate | Native | Fallback for hard scene continuation only; documented character drift | [4] |
| Qwen-Image-Edit-2509 | 20B instruction editor | Apache-2.0 | 57.70 GB | about 55-65 GB bf16, estimate | Native; dx8152 expansion workflow needs four custom packs | Excluded; superseded by 2511 for outpainting reliability | [5] |
| SDXL inpainting 0.1 | 1024-native 9-channel inpainting UNet | CreativeML Open RAIL++-M; card says research intent | 6.94 GB fp16 | about 12-16 GB at 2048, estimate | Diffusers format; needs a converter or the Fooocus patch | Excluded; malformed faces per its card, and 2048 is outside its 1024 training range | [10] |
| OmniGen2 | 7B unified instruction editor | Apache-2.0 | 31.22 GB | about 17 GB at default | Native | Excluded; about 2 MP working cap, and mask inpainting is not documented | [9] |
| DiffSynth-Studio with SuperOutpainting LoRA | Python framework plus a 0.31 GB LoRA on FLUX Kontext | Apache-2.0 framework and LoRA; FLUX dev base non-commercial | about 34.22 GB | about 30-35 GB bf16 at 2048, estimate | None | Excluded; a second runtime outside ComfyUI, and no benchmarks | [11] |
| LanPaint, ComfyUI-Angelo, ComfyUI-Inpaint-Nodes | Tools, not models | GPL-3.0, MIT, GPL-3.0 | code only | model-dependent | Custom nodes | Not models; LanPaint improves seams but does not protect a face from being re-rendered | [13][14][15] |

The Qwen-Image-ControlNet-Inpainting route is the only fully Apache-2.0 mask-based 20B option found [8][7]. Its ControlNet is 4,234,599,432 B, and the ComfyUI-ready base files are 40,861,031,488 B (transformer), 16,584,415,576 B (text encoder) and 253,806,246 B (VAE) [7][8]. A community report says it needs 48 GB for a 2048-long-edge run and failed on a 24 GB card [8]. No face-identity evaluation is published [8]. Its weights are on disk and its graph is already built [35][36].

### 3.2 Upscaling

| Rank | Model | Mechanism | Detail gain | Face behaviour | Licence | Download | VRAM at 2048x1536 | ComfyUI | Verdict | Sources |
|---|---|---|---|---|---:|---:|---|---|---|---|
| 1 | SeedVR2 3B fp16 | One-step diffusion restoration | Pores, eyelashes, fabric weave | Best identity balance of the generative options; no guarantee | Apache-2.0 | 7.29 GB | about 12-18 GB, estimate | Core nodes present | Chosen | [23][35][36] |
| 2 | HYPIR | One-step SD2.1 restoration | Modest texture; removes degradation | Conservative; preserves identity in the comparison found | Proprietary non-commercial | 6.33 GB | about 8-12 GB; 7.8 GB measured at 2048x1536 on a T4 | Custom node installed | First alternative | [24][35][36] |
| 3 | VOSR 2.0 | One-step 1.4B super-resolution | Strong structure claim; softest of the faithful group in the benchmark | Kept the same face in every portrait tested | Apache-2.0 | 6.97 GB | about 10-16 GB with tiling, estimate | Custom node, not installed | Reserve; Apache-2.0 but unlikely to add pore-level detail | [25] |
| 4 | CCSR | Two-stage diffusion super-resolution | High structure fidelity, little micro-detail | Low hallucination; no verified face study | Apache-2.0 weights; node has no licence file | 3.44 GB fp16 | about 8-12 GB with tiling, estimate | Custom node installed | Structure pass, not the only upscaler | [26][35][36] |
| 5 | HAT | Hybrid attention transformer | Sharpens existing edges only | Identity-safe by construction; no face study found | Apache-2.0 | 0.17 GB | about 4 GB at 2048 with 512 px tiles | Core through spandrel | Identity-safe control baseline | [27][35][36] |
| 6 | SwinIR | Swin transformer super-resolution | Less perceptual punch than HAT | Identity-safe by construction; no face study found | Apache-2.0 | 0.14 GB per model | about 3 GB at 2048 with tiles | Core through spandrel | Cheaper baseline; HAT is better | [28][35][36] |
| 7 | SUPIR | SDXL restoration with a large adapter | Highest texture gain | A forensic study found altered teeth edges, a changed ear shape and removed moles | Proprietary non-commercial | 9.60 GB | 20-28 GB untiled; up to 3072x3072 on a 24 GB card with fp8 and a tiled VAE | Core ComfyUI | Excluded for a child's face | [29][35][36] |
| 8 | InvSR | Diffusion-inversion one-step upscaler | Sharp perceptual output | Its own node documentation says it rewrites faces | S-Lab License 1.0, non-commercial | 2.72 GB with fp16 components | about 6-10 GB, estimate | Custom node installed | Excluded | [30][35][36] |
| 9 | Real-ESRGAN | RRDBNet GAN | Sharpens edges, invents high-frequency texture | No face prior; plastic skin; a separate GFPGAN pass exists | BSD-3-Clause | 67 MB | about 2 GB | Core through spandrel | Resolution-only last resort | [31][35][36] |
| 10 | 4x community ESRGAN (UltraSharp, Remacri, Siax) | RRDBNet 4x GAN | Fixed GAN detail | Remacri least harsh on skin; no face prior | CC BY-NC-SA 4.0 by a model comparison; UltraSharp confirmed | about 67 MB each | about 2 GB | Core through spandrel | Baseline only | [32][35][36] |
| 11 | AuraSR v2 | GigaGAN-style 4x upscaler | Built for generated images | No face evidence or identity test found | CC BY-SA 4.0; the card tag apache-2.0 conflicts | 2.47 GB | about 4-6 GB, estimate | Core through spandrel; may need spandrel_extra_arches | Rejected for a real portrait | [33][35][36] |
| 12 | LucidFlux | FLUX.1-dev restoration pipeline | Strong texture synthesis | Its own README says it hallucinates realistic details | FLUX.1 [dev] non-commercial | 25.88 GB | about 28 GB default, 8-12 GB offloaded | Custom node | Rejected; disqualifying warning for a face that must not change | [34] |

SeedVR2's own card warns that it can over-generate and oversharpen on lightly degraded inputs, which an extended photo is [23]. The 3B or the non-sharp 7B is therefore the safer starting point; the sharp 7B is not used for a child's face [23]. The independent benchmark of 27 September 2026 found SeedVR2 kept the same face in every portrait it tested [23]. That is one benchmark, not a guarantee.

## 4. Excluded candidates

This section states why each rejected candidate is out, and why several viable ones are not the first choice.

| Model or tool | Verdict | Reason | Sources |
|---|---|---|---|
| Qwen-Image 2.1 and its outpainting LoRA | Excluded | The Qwen Research License defines non-commercial as research or evaluation only; private family use is not clearly granted | [18] |
| SDXL inpainting 0.1 | Excluded | Trained at 1024; its card warns that faces and people may be malformed; a 2048 long edge is outside its training range | [10] |
| OmniGen2 | Excluded | Inputs above about 2 MP are resized down, and mask inpainting is not documented; a 2048x1536 canvas is 3.15 MP | [9] |
| Qwen-Image-Edit-2509 | Excluded | Superseded by 2511 for outpainting reliability; community users shelved it and report a much better success rate with 2511 | [5][6] |
| DiffSynth-Studio outpainting | Excluded | No ComfyUI integration, no benchmarks, and a second runtime outside the project's stack | [11] |
| FLUX.1 Kontext dev | Not chosen | No mask input; the official ComfyUI guide documents character drift when the prompt transforms the person; fallback only | [4] |
| FLUX.2 Klein 9B | Reserve | No mask; the community card warns faces can shift noticeably and texture transfer can be incomplete | [16] |
| FLUX.3 Image Klein | Reserve | Its LoRA was trained on 0.94-1.96 MP canvases, below the 2.18 MP frame; its own card reports 1 wrong result in 20 and a duplicated-knees failure | [17] |
| Z-Image Base | Reserve | No official outpainting; the community workflow reports no seam, face or quality benchmarks | [21] |
| Krea 2 Turbo and krea2-outpaint | Not chosen | Gated community licence, no official ComfyUI support, and a functional LoRA that ordinary importers do not handle | [22] |
| SUPIR | Excluded | A forensic study of 50 portraits found altered teeth edges, a changed ear shape and removed moles; not acceptable for a child's face | [29] |
| InvSR | Excluded | Its own node documentation says it invents detail and rewrites faces; fixed at 4x | [30] |
| AuraSR v2 | Rejected | Built for AI-generated images; no face-focused training or identity test was found | [33] |
| LucidFlux | Rejected | Its own README warns that it hallucinates realistic details and that output may differ from the input | [34] |
| Real-ESRGAN and the 4x community models as the final upscaler | Last resort or baseline | Purely regressive or fixed GAN priors; they preserve identity but cannot add true detail, and Real-ESRGAN can leave skin plastic | [31][32] |
| LanPaint, ComfyUI-Angelo, ComfyUI-Inpaint-Nodes | Not models | LanPaint improves mask-edge coherence but does not protect a face from being re-rendered; GPL-3.0 adds a licence obligation | [13][14][15] |

## 5. Licensing facts

| Model or component | Licence | Private home use | Commercial use | Record |
|---|---|---|---|---|
| FLUX.1 Fill dev | FLUX.1 [dev] Non-Commercial License v1.1.1 | Allowed: personal use, private entertainment, hobby projects | Not allowed without a BFL licence | Chosen; commercial restriction recorded |
| SeedVR2 3B and 7B | Apache-2.0 | Allowed | Allowed | Chosen |
| Qwen-Image-ControlNet-Inpainting and Qwen-Image base | Apache-2.0 | Allowed | Allowed | First alternative |
| HYPIR | Proprietary non-commercial from SupPixel Pty Ltd | Allowed | Not allowed | First alternative; the HF tag apache-2.0 conflicts with the LICENSE file |
| FLUX.2 Klein 4B and the fal outpaint LoRA | Apache-2.0 | Allowed | Allowed | Second alternative |
| FLUX.2 Klein 9B | FLUX Non-Commercial License | Allowed | Not allowed | Reserve |
| FLUX.3 Image Klein | FLUX Kommunity License v1.0 | Allowed | Allowed below the licence revenue threshold; military, surveillance and biometric uses restricted | Reserve |
| Qwen-Image-Edit 2511 and 2509 | Apache-2.0 | Allowed | Allowed | Reserve and excluded |
| Qwen-Image 2.1 | Qwen Research License, research or evaluation only | Not clearly granted | Not allowed | Excluded |
| Z-Image | Apache-2.0 | Allowed | Allowed | Reserve |
| Krea 2 Turbo | Krea 2 Community License, gated | Allowed | Allowed below the licence revenue threshold; content-filtering and safety-testing obligations | Not chosen |
| SDXL inpainting 0.1 | CreativeML Open RAIL++-M; the card says research purposes only | Allowed under RAIL++-M; the card wording is narrower | Allowed under RAIL++-M with use restrictions; the card wording conflicts | Excluded |
| SUPIR | Proprietary SUPIR Software License, non-commercial | Allowed | Not allowed | Excluded |
| InvSR | S-Lab License 1.0, non-commercial | Allowed | Not allowed | Excluded |
| VOSR 2.0 | Apache-2.0 for project materials; third-party components keep their terms | Allowed | Allowed for the project materials | Reserve |
| AuraSR v2 | CC BY-SA 4.0; the card tag says apache-2.0 | Allowed | Allowed with attribution and share-alike | Rejected |
| LucidFlux | FLUX.1 [dev] non-commercial | Allowed | Not allowed | Rejected |
| 4x-UltraSharp, Remacri, Siax | CC BY-NC-SA 4.0 by a model comparison; UltraSharp confirmed; Remacri's mirrors conflict | Allowed | Not allowed | Baseline only |
| Real-ESRGAN | BSD-3-Clause | Allowed | Allowed | Last resort |
| CCSR | Apache-2.0 weights; the ComfyUI node has no licence file | Allowed | Allowed for the weights | Not chosen |
| HAT and SwinIR | Apache-2.0 | Allowed | Allowed | Not chosen |
| ComfyUI | GPL-3.0 | Allowed | Allowed under GPL terms | Runtime |
| LanPaint and ComfyUI-Inpaint-Nodes | GPL-3.0 | Allowed | Allowed under GPL terms | Not used |
| ComfyUI-Angelo | MIT | Allowed | Allowed | Not used |

The FLUX.1 [dev] licence in detail [2]:

- Section 2(c) defines Non-Commercial Purpose and explicitly includes personal use for research, experiment and testing, personal study, private entertainment and hobby projects.
- Section 2(b) restricts the model to Non-Commercial Purposes; commercial activity needs a BFL licence.
- Section 2(d) says BFL claims no ownership rights in outputs and that outputs may be used for any purpose including commercial, except as expressly prohibited.
- Section 4(a) prohibits use of the model or any data produced by the model for commercial or production purposes.
- The conflict only affects selling outputs. Private home use is clearly inside the grant.

The FLUX.1 Fill repository is gated. The licence must be accepted by the account behind the vault token before the files download [1][35]. The first alternative, Qwen-Image-ControlNet-Inpainting, is fully Apache-2.0 and is already on disk [7][8][35].

## 6. Pipeline the notebook runs

The notebook uses GPU 1, the 96 GB RTX PRO 6000 (UUID `GPU-a44e514a-aa5b-2844-35f1-4be28e1921e5`), and a dedicated ComfyUI server on port 8189, which is free [35][36]. The server starts from the existing ComfyUI 0.42.0 root with its own input, output and temp directories, `HF_HUB_OFFLINE=1` and `--offline` [35][36]. No custom node is installed for the chosen pipeline.

The bench notebook extends one photo to 4:3 at 1704x1278 and to 16:9 at 2272x1278 with every viable extender, then upscales every extended frame 2x to 3408x2556 with every viable upscaler, and lays the results out as two matrices. The production frame for LTX-2.5 is the 4:3 result at 2048x1536. Every bench image, sidecar and grid is written under `tmp/media/henryk-urodziny-2026/extended/`; only a production run writes into `data/`.

### Step 1: extend to 4:3 with FLUX.1 Fill dev

- Load `IMG_8564.png` (962x1278) and pad it to 1704x1278 with `ImagePadForOutpaint`, left 371, right 371, top 0, bottom 0, feather 8 [1][12][36].
- Load `flux1-fill-dev.safetensors` with `UNETLoader`, `clip_l.safetensors` and `t5xxl_fp16.safetensors` with `DualCLIPLoader` (type `flux`), and `ae.safetensors` with `VAELoader` [1][3][36].
- Run `InpaintModelConditioning` into `KSampler`: steps 30, cfg 1.0, sampler `euler`, scheduler `normal`, denoise 1.0, `FluxGuidance` 30.0, fixed seed 42 [1][12][36]. The official inpainting blueprint uses 20 steps; the community portrait walkthrough proposes 30-40, so 30 is the starting value [1]. The same walkthrough proposes guidance 8-9 and strength 0.75-0.85 as levers if the fill is too strong or a seam appears at denoise 1.0 [1].
- The prompt describes the room and light visible in the photo and asks for the same floor, wall and light to continue into the added sides. It states that the child and the existing people must not change and that no new people may appear. The negative prompt is empty [1][12].
- Decode and save the raw 1704x1278 fill. The module then tone-matches the render to the photo and composites the original 962x1278 photo back at x=371 with an 8 px feather, using PIL, so the photo's interior pixels (all but the feathered edge) are bit-identical to the source [36].
- If the sides are weak or show a seam, run two passes: left 371 on a 1333x1278 canvas, then right 371 [1].

### Step 2: raise to 2048x1536 with SeedVR2 3B

- Load the composited 1704x1278 image, resize it to 2048x1536 with Lanczos, run `SeedVR2Preprocess`, and encode the result with `VAEEncodeTiled` [23][36].
- Run `SeedVR2Conditioning` into `KSampler` with 1 step, cfg 1.0, sampler `euler`, scheduler `simple`, denoise 1.0 and fixed seed 42, then `VAEDecodeTiled` and `SeedVR2PostProcessing` with the resized input as `original_resized_images` and colour correction `lab` [36][23]. The local blueprint defaults to the int8 3B weights, so the loader must be pointed at `seedvr2_3b_fp16.safetensors` [35][36].
- Save the raw 2048x1536 frame. The module then composites the original photo, resampled once to 1156x1536 with Lanczos, back at x=446 with an 8 px feather. The child's pixels are therefore a resample, not a regeneration [36].
- Write the PNG with a `.md` sidecar naming the source, both models, the settings, the seed, the size and the peak VRAM, and a checkpoint a rerun restores from [36]. The bench output goes under `tmp/media/henryk-urodziny-2026/extended/`; a production run may write into `data/processed/henryk-urodziny-2026/extended/` after the Star Colonel accepts the result.

### Verification

- The output is 4:3; the production frame is 2048x1536, and the bench tile is 3408x2556.
- A 100% face crop matches the source, resampled once, with no facial texture invented by either model.
- The added area contains no invented people and no second scene.
- Floor, wall and light continue across the seam at 100% zoom.
- The original files in `data/raw/` and `data/external/` are unchanged, and no photo copy remains in the server's input, output or temp folder.

## 7. Caveats and confidence

| Statement | Confidence | Basis |
|---|---|---|
| Candidate order | Medium | Cited documentation and community reports; no test on a child's face |
| File names and sizes | High | Hugging Face API file trees and the local inventory read on 2026-10-25 |
| Licence text | High | FLUX licence read from the public BFL repository; the others from their repositories and licence files |
| Local ComfyUI nodes present | High | ComfyUI 0.42.0 source, blueprints and the CPU import check on 2026-10-25 |
| VRAM estimates | Low | Published reports and model cards, not measured on this workstation |
| FLUX Fill quality at 43.5% new area | Low | Community reports; the 40% guidance is close to the limit |
| SeedVR2 identity safety | Medium | One independent benchmark and community comparisons; no guarantee, so the guard-rail composite removes the risk |
| One pass versus two passes | Low | Untested |
| Output path rule | High | The Star Colonel's rule of 2026-10-25 03:18: bench output under `tmp/media/`, production only under `data/` |

- No candidate was tested on the project's photos. All quality statements come from model cards, papers, documentation and community reports.
- The FLUX Fill download was refused at 02:14 and 03:0x. The transformer finished at 23,804,922,408 B and passed a safetensors header and tensor-extent check at 03:26; the VAE and both text encoders are still absent and the vault was locked at the last check (03:30), so the chosen route is not runnable yet [35][39]. A partial download is not a working model.
- The FLUX.1 [dev] licence's output clauses conflict; private use is unaffected.
- The 43.5% new area is just above the 40% guidance, so the two-pass fallback matters.
- No upscaler guarantees face identity. The composite of the original photo back is mandatory, not optional.
- The child's photo is personal data. Every run is local, and no image is sent to an external service.
- The chosen path installs no custom node, so the shared ComfyUI venv is not modified. The upscale alternative HYPIR uses a node that is already installed and imported; the Qwen alternative uses core nodes and weights already on disk.
- The shared venv is used by every server; installing or upgrading a pack can replace numpy, opencv or torch and break the existing animation packs [35].
- The FLUX.2 Klein 4B second alternative needs the fal LoRA and a green-fringe check; its card reports no face or identity evaluation [19].
- The source sidecar has no scene description, so the outpainting prompt must be written after viewing the photo [38].

## 8. Sources

1. FLUX.1 Fill dev model card, file tree, ComfyUI tutorial, ComfyUI wiki tutorial, portrait walkthrough and ComfyUI issue 6765 - https://huggingface.co/black-forest-labs/FLUX.1-Fill-dev , https://huggingface.co/api/models/black-forest-labs/FLUX.1-Fill-dev/tree/main?recursive=true , https://docs.comfy.org/tutorials/flux/flux-1-fill-dev , https://comfyui-wiki.com/en/tutorial/advanced/image/flux/flux-1-dev-fill , http://theneuralbase.com/flux/learn/intermediate/flux-fill-quality/ , https://github.com/Comfy-Org/ComfyUI/issues/6765
2. FLUX.1 [dev] Non-Commercial License v1.1.1 - https://github.com/black-forest-labs/flux/blob/main/model_licenses/LICENSE-FLUX1-dev
3. comfyanonymous/flux_text_encoders file tree - https://huggingface.co/api/models/comfyanonymous/flux_text_encoders/tree/main
4. FLUX.1 Kontext: ComfyUI tutorial, model card, file tree, paper and SuperOutpainting LoRA - https://docs.comfy.org/tutorials/flux/flux-1-kontext-dev , https://huggingface.co/black-forest-labs/FLUX.1-Kontext-dev , https://huggingface.co/api/models/black-forest-labs/FLUX.1-Kontext-dev/tree/main?recursive=true , https://arxiv.org/pdf/2504.09697 , https://huggingface.co/DiffSynth-Studio/FLUX.1-Kontext-dev-lora-SuperOutpainting
5. Qwen-Image-Edit 2509: model card, file tree, dx8152 workflow, ComfyUI docs and community reports - https://huggingface.co/Qwen/Qwen-Image-Edit-2509 , https://huggingface.co/api/models/Qwen/Qwen-Image-Edit-2509/tree/main?recursive=true , https://huggingface.co/dx8152/Qwen-Edit-2509-workflow , https://docs.comfy.org/tutorials/image/qwen/qwen-image-edit , https://genai.stackexchange.com/questions/2784 , https://civarchive.com/models/2287120/qwen2511-outpaint-everything?modelVersionId=2573887
6. Qwen-Image-Edit 2511: model card, file tree, ComfyUI docs, official Expand Image workflow and outpainting success report - https://huggingface.co/Qwen/Qwen-Image-Edit-2511 , https://huggingface.co/api/models/Qwen/Qwen-Image-Edit-2511/tree/main?recursive=true , https://docs.comfy.org/tutorials/image/qwen/qwen-image-edit-2511 , https://comfy.org/workflows/f8cf4feac2e9-f8cf4feac2e9/ , https://civarchive.com/models/2287120/qwen2511-outpaint-everything?modelVersionId=2573887
7. Qwen-Image base: model card, Comfy-Org file tree and VRAM measurements - https://huggingface.co/Qwen/Qwen-Image , https://huggingface.co/api/models/Comfy-Org/Qwen-Image/tree/main , https://ai-fukugyo-tool.com/tools/en/vram/image-video/qwen-image/
8. InstantX/Qwen-Image-ControlNet-Inpainting: model card, file tree and community report - https://huggingface.co/InstantX/Qwen-Image-ControlNet-Inpainting , https://huggingface.co/api/models/InstantX/Qwen-Image-ControlNet-Inpainting/tree/main?recursive=true , http://mp.weixin.qq.com/s?__biz=MzU2Nzc2NjAxOA==&mid=2247489622&idx=1&sn=95a6a53767b4dbf165c16687da575db0
9. OmniGen2: model card, file tree, ComfyUI tutorial and day-0 blog - https://huggingface.co/OmniGen2/OmniGen2 , https://huggingface.co/api/models/OmniGen2/OmniGen2/tree/main?recursive=true , https://docs.comfy.org/tutorials/image/omnigen/omnigen2 , https://blog.comfy.org/p/omnigen2-native-support-in-comfyui
10. SDXL inpainting 0.1: model card, file tree, ComfyUI basic inpaint tutorial and Adobe/Fooocus patch nodes - https://huggingface.co/diffusers/stable-diffusion-xl-1.0-inpainting-0.1 , https://huggingface.co/api/models/diffusers/stable-diffusion-xl-1.0-inpainting-0.1/tree/main?recursive=true , https://docs.comfy.org/tutorials/basic/inpaint , https://github.com/Acly/comfyui-inpaint-nodes
11. DiffSynth-Studio: SuperOutpainting LoRA card, file tree and framework repository - https://huggingface.co/DiffSynth-Studio/FLUX.1-Kontext-dev-lora-SuperOutpainting , https://huggingface.co/api/models/DiffSynth-Studio/FLUX.1-Kontext-dev-lora-SuperOutpainting/tree/main?recursive=true , https://github.com/modelscope/DiffSynth-Studio
12. ComfyUI outpainting: docs, core nodes source, ComfyTV commit and repository - https://docs.comfy.org/tutorials/basic/outpaint , https://github.com/comfyanonymous/ComfyUI/blob/master/nodes.py , https://github.com/jtydhr88/ComfyTV/commit/acde8fc729e9144784ff0b9e517e9a0d592a5e20 , https://github.com/comfyanonymous/ComfyUI
13. LanPaint: repository, model page and Qwen 2511 workflow - https://github.com/scraed/LanPaint , https://huggingface.co/charrywhite/LanPaint , https://civarchive.com/models/2287120/qwen2511-outpaint-everything?modelVersionId=2573887
14. ComfyUI-Angelo: repository and article - https://github.com/shootthesound/ComfyUI-Angelo , https://www.creativeainews.com/blog/comfyui-angelo-outpainting-upscaling-2026/
15. ComfyUI-Inpaint-Nodes: repository and repository metadata - https://github.com/Acly/comfyui-inpaint-nodes , https://api.github.com/repos/Acly/comfyui-inpaint-nodes
16. FLUX.2 Klein: BFL model page, 9B and 4B model cards, file trees, ComfyUI tutorial, uncrop LoRA card and 4B outpainting workflow - https://bfl.ai/models/flux-2-klein , https://huggingface.co/black-forest-labs/FLUX.2-klein-9B , https://huggingface.co/black-forest-labs/FLUX.2-klein-4B , https://huggingface.co/api/models/black-forest-labs/FLUX.2-klein-9B/tree/main?recursive=true , https://huggingface.co/api/models/black-forest-labs/FLUX.2-klein-4B/tree/main?recursive=true , https://docs.comfy.org/tutorials/flux/flux-2-klein , https://civarchive.com/models/2106308/uncropinpaintoutpaint-with-context-image-for-f2-klein-9b-qwen-image-edit-lora?modelVersionId=2620761 , https://www.floyo.ai/workflows/flux-2-klein-4b-for-image-outpaintin-9kg88ecsdrj1
17. FLUX.3 Image Klein: model card, file tree, ComfyUI tutorial, ausboss Outpaint LoRA card and file tree - https://huggingface.co/black-forest-labs/flux-3-image-klein , https://huggingface.co/api/models/black-forest-labs/flux-3-image-klein/tree/main?recursive=true , https://docs.comfy.org/tutorials/flux/flux-3-klein , https://huggingface.co/ausboss/FLUX-3-Image-Klein-Outpaint-LoRA , https://huggingface.co/api/models/ausboss/FLUX-3-Image-Klein-Outpaint-LoRA/tree/main?recursive=true
18. Qwen-Image 2.1: model card, file tree, licence, ComfyUI tutorial, outpainting workflow and ausboss LoRA - https://huggingface.co/Qwen/Qwen-Image-2.1 , https://huggingface.co/api/models/Qwen/Qwen-Image-2.1/tree/main?recursive=true , https://huggingface.co/Qwen/Qwen-Image-2.1/blob/main/LICENSE , https://docs.comfy.org/tutorials/image/qwen/qwen-image-2-1 , https://civarchive.com/models/2964810?modelVersionId=3371201 , https://huggingface.co/ausboss/Qwen-Image-2.1-Outpaint-LoRA
19. fal/flux-2-klein-4B-outpaint-lora: model card, file tree, mirror and workflows - https://huggingface.co/fal/flux-2-klein-4B-outpaint-lora , https://huggingface.co/api/models/fal/flux-2-klein-4B-outpaint-lora/tree/main?recursive=true , https://huggingface.co/xocialize/outpaint-FLUX.2-klein-4B-lora , https://www.mimicpc.com/workflows/mimicpc-outpaint-studio-infinite-canvas-image-expansion , https://www.floyo.ai/workflows/flux-2-klein-4b-for-image-outpaintin-9kg88ecsdrj1
20. ComfyUI Expand Image workflow (Qwen-Image-Edit 2511 green matte) - https://comfy.org/workflows/f8cf4feac2e9-f8cf4feac2e9/
21. Z-Image: model card, file tree, ComfyUI tutorial, day-0 blog, community outpaint workflow and InvokeAI guide - https://huggingface.co/Tongyi-MAI/Z-Image , https://huggingface.co/api/models/Tongyi-MAI/Z-Image/tree/main?recursive=true , https://docs.comfy.org/tutorials/image/z-image/z-image , https://blog.comfy.org/p/z-image-day-0-support-in-comfyui , https://civitaiarchives.com/models/2396418?modelVersionId=2694484 , https://invoke-ai.github.io/InvokeAI-7/users-guide/models/local-models/z-image/
22. Krea 2: krea2-outpaint card and file tree, Krea 2 Turbo card and file tree, unofficial node and licensing page - https://huggingface.co/yijunwang2/krea2-outpaint , https://huggingface.co/api/models/yijunwang2/krea2-outpaint/tree/main?recursive=true , https://huggingface.co/krea/Krea-2-Turbo , https://huggingface.co/api/models/krea/Krea-2-Turbo/tree/main?recursive=true , https://github.com/RealRebelAI/ComfyUI-Rebels-Krea2-Outpaint , https://www.krea.ai/krea-2-licensing
23. SeedVR2: 7B and 3B model cards, Comfy-Org file tree, SeedVR code, ComfyUI tutorial, nodes_seedvr.py, node page and independent benchmark - https://huggingface.co/ByteDance-Seed/SeedVR2-7B , https://huggingface.co/ByteDance-Seed/SeedVR2-3B , https://huggingface.co/Comfy-Org/SeedVR2 , https://huggingface.co/api/models/Comfy-Org/SeedVR2/tree/main , https://github.com/ByteDance-Seed/SeedVR , https://docs.comfy.org/tutorials/utility/seedvr2 , https://raw.githubusercontent.com/comfyanonymous/ComfyUI/master/comfy_extras/nodes_seedvr.py , https://comfy.icu/node/SeedVR2 , https://www.gocrazy.ai/ai-image-upscaler-benchmark
24. HYPIR: repository, licence, model card, file tree, EricRollei node, flybirdxx node, SD2.1 mirror, SeedVR2 plus HYPIR comparison and node page - https://github.com/XPixelGroup/HYPIR , https://github.com/XPixelGroup/HYPIR/blob/main/LICENSE , https://huggingface.co/lxq007/HYPIR , https://huggingface.co/api/models/lxq007/HYPIR/tree/main?recursive=true , https://github.com/EricRollei/HYPIR-ComfyUI , https://github.com/flybirdxx/ComfyUI-HYPIR , https://huggingface.co/EricRollei/SAI-SD2.1-for-HYPIR , https://dodistyo.github.io/posts/seedvr2-hypir-photo-restoration-duo/ , https://comfy.icu/extension/EricRollei__HYPIR-ComfyUI
25. VOSR 2.0: repository, model card, file tree, ComfyUI node, ComfyUI wiki news, GoCrazy benchmark and project page - https://github.com/cswry/VOSR , https://huggingface.co/CSWRY/VOSR , https://huggingface.co/api/models/CSWRY/VOSR/tree/main?recursive=true , https://github.com/ylchen333/ComfyUI-VOSR2 , https://comfyui-wiki.com/en/news/2026-09-19-comfyui-vosr2 , https://www.gocrazy.ai/ai-image-upscaler-benchmark , https://cswry.github.io/vosr2/
26. CCSR: repository, licence, Kijai weights, ComfyUI node, comparison and v2 repost - https://github.com/csslc/CCSR , https://github.com/csslc/CCSR/blob/CCSR-v2.0/LICENSE , https://huggingface.co/Kijai/ccsr-safetensors , https://github.com/kijai/ComfyUI-CCSR , https://github.com/MohamedAbdallah-14/prompt-to-asset/blob/main/docs/research/17-upscaling-refinement/17b-supir-ccsr-diffbir-refinement.md , https://huggingface.co/kharma1/ccsr_v2_repost
27. HAT: repository, licence, Acly weights, spandrel and third-party model card - https://github.com/XPixelGroup/HAT , https://raw.githubusercontent.com/XPixelGroup/HAT/main/LICENSE , https://huggingface.co/Acly/hat , https://github.com/chaiNNer-org/spandrel , https://huggingface.co/AEmotionStudio/ai-upscale-models
28. SwinIR: repository, release weights, licence, spandrel and third-party model card - https://github.com/JingyunLiang/SwinIR , https://github.com/JingyunLiang/SwinIR/releases/tag/v0.0 , https://raw.githubusercontent.com/JingyunLiang/SwinIR/main/LICENSE , https://github.com/chaiNNer-org/spandrel , https://huggingface.co/AEmotionStudio/ai-upscale-models
29. SUPIR: repository, licence, Kijai weights, SDXL base, ComfyUI node, ComfyUI PR and forensic study - https://github.com/Fanghua-Yu/SUPIR , https://github.com/Fanghua-Yu/SUPIR/blob/master/LICENSE , https://huggingface.co/Kijai/SUPIR_pruned , https://huggingface.co/stabilityai/stable-diffusion-xl-base-1.0 , https://github.com/kijai/ComfyUI-SUPIR , https://github.com/comfyanonymous/ComfyUI/pull/13250 , https://dfrws.org/wp-content/uploads/2026/03/DFRWS_EU_2026_paper_123.pdf
30. InvSR: repository, model card, licence, SD-Turbo, ComfyUI node and node page - https://github.com/zsyOAOA/InvSR , https://huggingface.co/OAOA/InvSR , https://huggingface.co/OAOA/InvSR/blob/main/LICENSE , https://huggingface.co/stabilityai/sd-turbo , https://github.com/yuvraj108c/ComfyUI_InvSR , https://comfy.icu/node/InvSRSampler
31. Real-ESRGAN: repository, releases, licence, spandrel and GFPGAN routing article - https://github.com/xinntao/Real-ESRGAN , https://api.github.com/repos/xinntao/Real-ESRGAN/releases , https://github.com/xinntao/Real-ESRGAN/blob/master/LICENSE , https://github.com/chaiNNer-org/spandrel , https://dev.to/wladradchenko/two-enhancers-one-frame-routing-faces-to-gfpgan-and-the-rest-to-real-esrgan-518g
32. 4x community ESRGAN models: mirror, UltraSharp card, Remacri mirror, model comparison, SeaArt card, upscaler comparison and spandrel - https://huggingface.co/uwg/upscaler , https://huggingface.co/Kim2091/UltraSharp , https://huggingface.co/LyliaEngine/4x_foolhardy_Remacri , https://chunks.md/docs/image-upscale/models , https://www.seaart.ai/app/d71m3nde878c73b1m1sg , https://aiofm.info/en/tools/upscaler-comparison , https://github.com/chaiNNer-org/spandrel
33. AuraSR v2: model card, licence, repository, blog, ComfyUI node and spandrel - https://huggingface.co/fal/AuraSR-v2 , https://huggingface.co/fal/AuraSR-v2/raw/main/LICENSE.md , https://github.com/fal-ai/aura-sr , https://blog.fal.ai/aurasr-v2/ , https://github.com/alexisrolland/ComfyUI-AuraSR , https://github.com/chaiNNer-org/spandrel
34. LucidFlux: repository, model card, connector, ComfyUI node and dependencies - https://github.com/W2GenAI-Lab/LucidFlux , https://huggingface.co/W2GenAI/LucidFlux , https://huggingface.co/smthem/LucidFLUX-connector , https://github.com/smthemex/ComfyUI_LucidFlux , https://huggingface.co/Comfy-Org/flux1-dev , https://huggingface.co/Owen777/UltraFlux-v1 , https://huggingface.co/google/siglip2-so400m-patch16-512 , https://huggingface.co/lxq007/DiffBIR
35. Local integration checkpoint and download checkpoint - `tmp/workflows/image-extender/research/local.json`, `tmp/workflows/image-extender/download.json`
36. Local ComfyUI 0.42.0 source, blueprints and extender setup - `models/photo-animation/ComfyUI/nodes.py`, `models/photo-animation/ComfyUI/comfy_extras/nodes_seedvr.py`, `models/photo-animation/ComfyUI/comfy_extras/nodes_controlnet.py`, `models/photo-animation/ComfyUI/comfy_extras/nodes_mask.py`, `models/photo-animation/ComfyUI/blueprints/Image Inpainting (Flux.1 Fill Dev).json`, `models/photo-animation/ComfyUI/blueprints/Upscale Video (SeedVR2 3B Int8).json`, `tmp/workflows/image-extender/setup-extender.json`
37. LTX-2.5 setup JSON - `tmp/workflows/image-to-video/setup-chosen.json`
38. Source photo sidecar - `data/interim/henryk-urodziny-2026/IMG_8564.md`
39. FLUX Fill download log and staging file - `logs/image-extender-download-flux.log`, `models/photo-animation/.hf-staging-flux/`

<!-- complete -->
