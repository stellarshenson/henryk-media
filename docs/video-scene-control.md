# Scene control playbook - MiniMax H3 and LTX-2.5

Status: DRAFT for internal review, 2026-10-25.

## 1. Common levers

Both models take scene and camera control from the prompt.

- Camera stillness is prompt text; neither graph has a camera parameter [2][7][16]
- State holds as fact: "camera holds a static shot" [1][19][27]
- One action per clip [29]
- Image-to-video: describe motion only, never re-describe the photo [28]
- Negations need a negative branch above cfg 1 [9]; H3 none [1], LTX one [14]
- LTX strength 1.0 pins frame 0 [6][14]; H3 first_frame stretches to canvas [17][5]
- One continuous take: no "cut to", no named extra person [7][28]
- Aspect and length: H3 768/1344, 17k+5 [2][17]; LTX 32-pixel, 8k+1 [11]

## 2. MiniMax H3

H3 writes video and audio jointly under a positive-only guider.

- cfg 1, no negative branch; ban lists add the concept [1]
- Three fields, blank-line separated; dialogue only in `<d>[Language] ...</d>` with `(S1)` IDs [1][32]
- 24 fps, 17k+5: 141 = 5.875 s, 158 = 6.583 s; 144 becomes 158 [17]
- res_multistep simple, 20 steps; speech needs 12+; 8 turbo weakens audio [2]

```text
integrated_multimodal_description: For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced. The camera holds a static shot throughout. A boy holds a picture book. He blinks once and smiles slightly, then settles. The room and framing stay exactly as they are. Exactly one person is visible for the entire shot.

overall_soundscape: Quiet birthday-party room tone, faint chatter from the next room. No voices, no singing, no words.

non_diegetic_music: N/A
```

- Soundscape carries silence; N/A for true silence; "no dialogue" removes speech only, "no audio" all [1][20]
- Absence: "exactly one person is visible"; "lips remain closed" [20][22]
- last_frame or AddGuide at round(seconds × 24) [3][4][5]

Avoid negative-prompt syntax, simultaneous group action and quoted speech; state exclusions as plain clauses [1][20][21][28].

| Failure | Lever |
|---|---|
| Lips move | Closed-lips clause [24]; no-voice soundscape [1] |
| New people | One-person sentence plus fixed room sentence [19][22] |
| Camera drift | "Static Shot" in shot text [19][32] |
| Identity drift | Ref2VA [4] |

## 3. LTX-2.5

LTX-2.5 has a negative branch and separate video, audio and modality guidance.

- Negative: 5-8 concepts, inert at cfg 1; local list holds "silent or muted audio" [9][15][18]
- Add "static, frozen, no motion" to image-to-video negatives only when the source image is ambiguous; drop "static frame" for fast-motion shots [9]
- Video cfg 3.0-3.5 (2.0-5.0; not 7.0); audio 7.0; modality 3.0, 1.0 disables sync [8][10]
- STG 1.0 block 28 preserves motion beyond CFG [12][30]; block 28 is the LTX-2.3 preset, and the local 2.5 graph uses 28 [18]
- Strength 1.0 pins frame 0 [6][14]; scheduler 2.05/0.95/stretch/0.1, latent wired [13]; rescale 0.7 absent locally [12][18]
- Steps 20-50 T2V, 60-80 I2V, local 30 [8]; 8k+1: 121 = 5.04 s, 145 = 6.04 s; 144 invalid [11]
- Prompt: one 4-8 sentence present-tense paragraph [7]

```text
A static shot of a young boy holding a glass jar up to the camera. He keeps the jar, the room and the framing exactly as they are; only his face moves. He blinks once and one corner of his mouth rises into a small smile, then settles. The camera remains fixed on a tripod and does not move, zoom or reframe. Natural room tone only, with no dialogue or voice.
```

| Failure | Lever |
|---|---|
| Zoom | "A static shot..." [26]; zoom in negatives [9]; 19B LoRA test only [16] |
| Extra people | One dominant action per shot [28] |
| Morph from source | Motion-only prompt [28] |
| Speech | No quoted dialogue; ambience only [7]; "added dialogue" in the default negatives [15] |

## 4. Ranked test plan

Cheapest first; one H3 render costs about 11-23 minutes in local runs.

1. **H3 three-field silence prompt.** IMG_8564, seed 42, 141 frames, section 2 template. Proves positive audio fields remove speech
2. **H3 one-person and Static Shot clauses.** IMG_8564, 5 seeds. Proves new-face suppression and camera hold
3. **H3 smile beat.** IMG_8732. Baseline, trigger, response, settle [23]. Proves a smile rises and settles
4. **LTX negative rebuild.** IMG_8840, 121 frames. Eight concepts: flicker, frame jump, temporal inconsistency, character morphing, identity drift, camera movement, zoom, extra person. Proves list length is not needed
5. **LTX prompt and static probe.** IMG_8840. Compare motion with current-clips-motion.json. Proves wording reduces zoom
6. **H3 endpoint anchor.** IMG_8840, 158 frames, last_frame or AddGuide. Proves anchoring holds the room

## 5. Sources

Seen 2026-10-25 unless dated.

Official:

[1] https://docs.comfy.org/tutorials/video/minimax/minimax-h3-prompt-guide
[2] https://docs.comfy.org/tutorials/video/minimax/minimax-h3
[3] https://docs.comfy.org/built-in-nodes/MiniMaxH3AddGuide
[4] https://docs.comfy.org/tutorials/video/minimax/minimax-h3-multiframe
[5] https://docs.comfy.org/tutorials/video/minimax/minimax-h3-native
[6] https://docs.ltx.io/open-source-model/usage-guides/image-to-video
[7] https://docs.ltx.io/open-source-model/usage-guides/prompting-guide
[8] https://website.ltx.io/blog/comfyui-workflow-guide
[9] https://website.ltx.io/blog/negative-prompts
[10] https://website.ltx.io/blog/multimodal-conditioning
[11] https://huggingface.co/Lightricks/LTX-2.5
[12] https://raw.githubusercontent.com/Lightricks/LTX-2/main/packages/ltx-pipelines/src/ltx_pipelines/utils/constants.py
[13] https://raw.githubusercontent.com/Comfy-Org/embedded-docs/main/comfyui_embedded_docs/docs/LTXVScheduler/en.md
[14] https://huggingface.co/docs/diffusers/api/pipelines/ltx2
[15] https://raw.githubusercontent.com/huggingface/diffusers/main/src/diffusers/pipelines/ltx2/utils.py - undated
[16] https://website.ltx.io/model/capabilities/video-motion-control
[31] https://huggingface.co/MiniMaxAI/MiniMax-H3
[32] https://huggingface.co/MiniMaxAI/MiniMax-H3/raw/main/docs/VIDEO_PROMPT_WRITING_GUIDE_base_en.md

Local:

[17] /home/lab/workspace/private/henryk/henryk-media/models/photo-animation/ComfyUI/comfy_extras/nodes_minimax_h3.py
[18] /home/lab/workspace/private/henryk/henryk-media/tmp/workflows/ltx25-preview/render-settings.json

Community:

[19] https://minimaxh3.tv/blog/image-to-video-prompts-minimax-h3 - 2026-08-05
[20] https://cdn.jsdelivr.net/gh/Rimagination/h3lite@HEAD/references/prompt-writing.md - undated
[21] https://hellogen.ai/blog/minimax-h3-prompt-guide-short-drama/ - 2026-10-18
[22] https://www.seedance.tv/blog/minimax-h3-negative-prompt-comfyui - 2026-09-10
[23] https://www.seedance.tv/blog/minimax-h3-microexpression-prompts - 2026-09-10
[24] https://github.com/zenstory-ai/drama-skills/pull/169 - 2026-09-15
[25] https://github.com/hako-mikan/comfyui-minimax-h3-negpip - undated
[26] https://huggingface.co/Lightricks/LTX-2.5/discussions/54 - 2026-08-17
[27] https://fal.ai/learn/tools/how-to-use-ltx-2-5 - 2026-08-18
[28] https://www.earngenix.com/tutorials/ltx-2-5-prompt-fix-comfyui - 2026-08
[29] https://aicraftpad.com/articles/animate-still-image-with-character-consistency/ - undated

Paper:

[30] https://arxiv.org/abs/2411.18664 - STG, 2024-11-27

### 5.1 Claims with no verifiable source

- 19B static LoRA on 22B dev: no 22B camera LoRA listed [16]
- LoRA strength: no published value
- Modality 1.0 or audio cfg 1.0 suppressing lips: untested
- 0.7 strength adding motion on 22B dev: documented for distilled only [6]
- H3 "no audio" lowering mouth movement: unmeasured [20]
- 19B/22B mixing warning: third-party, not Lightricks
- NegPiP [25] as a lip-movement lever: its README documents negative conditioning, not lips, mouth, speech or lip-sync
- STG 0.5 when shimmer appears: no source states this value
- Block 28 as an LTX-2.5 default: 28 is the LTX-2.3 preset [12]; only the local 2.5 graph states 28 [18]
