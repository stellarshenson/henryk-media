# MiniMax H3 prompting

Status: RESEARCH SYNTHESIS, 2026-10-26. Merges the official, community and technique checkpoints. Every factual statement carries a source number; findings with no primary source are marked unconfirmed.

## 1. Model and prompt

The official H3 prompt for image-to-video is one structured English prompt read by a 32B vision-language encoder [1].

- The text encoder is the full pretrained Qwen3-VL-32B, passing layer-50 hidden states to the H3 Omni Transformer; visual inputs also reach the VisualVAE, and audio is encoded solely by the AudioVAE [1]
- The ComfyUI image-to-video node passes the first and last frame images into the tokenizer with the prompt [6]
- The I2VA prompt is a fixed first-line alignment sentence, one blank line, then three labelled fields: `integrated_multimodal_description`, `overall_soundscape`, `non_diegetic_music` [2]
- The exact alignment sentence names the picture at 0.00 seconds: "For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced." [2]
- The body follows one continuous path: first-frame anchor, action onset, continuous development, result or reaction [2]
- `overall_soundscape` is 1-4 English sentences and `non_diegetic_music` is 1-3; `N/A` is reserved for complete silence, not for "no dialogue" [2]
- The base guide sets no word target (absence finding) [2]
- The official skill says to match the described action duration to the requested clip length [3]
- The hosted API caps the text at 7,000 characters [4]
- Local generation snaps the frame count to the 17k+5 grid at 24 fps; a nominal 10 s request becomes 243 frames, 10.125 s, and the trained range is about 124-362 frames, 5-15 s [6][8]
- The ComfyUI template stretches `first_frame` to the canvas without preserving aspect ratio and centre-crops `last_frame`; motion is generated between the optional keyframes [7]
- An FL2VA prompt spends its words on the path between the frames, not on describing the two pictures [33]
- MiniMax states H3-Context-IR is critical to final output quality; it is not in the open release [1]
- Structure matters more than wording: a reply in the model's discussion says structure and label consistency matter, exact template wording does not [11]
- Official prompt length varies: the model card's I2VA example reports 12,800 prompt tokens [1], while a community count of 45 official examples gives a median near 130 Chinese characters (unconfirmed) [32]
- The hosted API suggests bracketed camera tags such as `[pan]`, `[zoom]` and `[static]` [4], while the open-weight guide requires natural-language camera wording inside the shot [2]; the hosted page does not say it applies to the open weights (unconfirmed)

## 2. Negative prompt

The official path has no negative prompt [1][9][10].

- The released checkpoints are CFG-distilled, so classifier-free guidance is not an adjustable control [1]
- The official ComfyUI graph runs `BasicGuider` at cfg 1 with no negative branch [9]
- The SGLang integration states that a generic negative prompt and guidance scales do not apply to H3 [10], and MiniMax's local deployment guide requires `--cfg-parallel-size` 1 [5]
- The official prompt guide contains no negative-prompt section and documents no negative field (absence finding) [2]; the official guidance is positive wording, because ban lists add unwanted concepts [9]
- A third-party test reports that appending "no matches" did not remove fire (low confidence, unconfirmed) [18]
- The documented workarounds are community patches: NegPiP sign-flips the value vectors of negative tokens inside joint attention [16], and H3 Shadow Negative adds a repulsion branch at about 15-30% more inference [17]
- Neither workaround reports an independent benchmark (unconfirmed) [16][17]

## 3. Motion over 10 s

Motion is controlled by positive description, keyframes and step count [1][7][8]. No official source gives a pacing rule for 10 s (unconfirmed).

| Shape | Effect |
|---|---|
| One action with a visible start and end [20] | change over time instead of a held pose |
| One camera move with type, amplitude and speed [2] | the camera does not fall back to a float |
| A rate or count in the action [24] | paces the event; duration is read literally as speed [23] |
| No camera cue [19] | static or gently floating frame |
| Appearance-only description [20] | no change over time |
| Identical first and last frames [13] | near-static renders, water included |
| 8-step Turbo LoRA [7][8] | softer motion and audio |

- Over 10 s the official shape is one continuous path, not a beat list [2]
- The official skill requires the described action to fill the requested clip length [3]
- H3's default is restrained: in a fixed-seed six-ad comparison it changed the fewest pixels of the models tested [21]
- A community pacing guide maps 10 s to one or two peaks and one or two braking moments (low confidence) [22]
- A second community budget allows two beats under 6 s and three on longer clips (unconfirmed) [19]
- Community recipes converge on one main action and one camera move [20], or one dominant camera movement, one primary action and one short clause for what stays fixed [12]
- Most motion gains arrive by step 16; speech and timbre need 12 or more steps, and little changes past 50 [8]; native 20 steps was the reference, and 12 steps was visibly weaker in harder scenes [21]
- A constraint sentence narrows drift rather than removing it [25]
- The identical-keyframe freeze has no official fix; MiniMax replied that it had not been investigated (paraphrased) [13]

## 4. Speech and lips

Speech is requested by structure, not by mood words: a speaker ID and a `<d>` line produce speech, and silence is the same structure without them [2][26].

| Goal | Wording that works |
|---|---|
| Start speech | speaker ID, a verb such as "says", and the line inside `<d>` [2][26] |
| Stop speech | no speaker ID and no `<d>`; fill `overall_soundscape` with room tone and action sound [2][9] |
| Hold a visible face | "lips remain completely closed" [2][29] |
| Avoid the mouth | turn the face away or place the speaker out of frame [29] |
| Recover a talking take | generate silent footage and add narration in editing [31] |

- Only the content inside `<d>` is spoken; characters who never vocalise receive no speaker ID [2]
- Ref2VA animates a face to speak with mouth movements syncing to the supplied dialogue [1]
- A silent performance still produces room tone and ambience [26]; a quoted line plus a described voice produced speech that ASR transcribed word for word [26]
- Repeated "No dialogue" and "silent!!!!!!" did not stop the model speaking [14]
- A full non-verbal sound-design block produced a silent clip on a Chinese forum; removing it produced speech, and stronger prohibitions did not stop it (unconfirmed) [27]
- ComfyUI guidance is to fill both audio fields explicitly when unwanted speech appears [9]
- Provider docs offer "She does not speak." or "No spoken dialogue." and warn that without it the model may invent speech [28], but the same intent failed in an HF report; neither is a controlled test (unconfirmed) [14][28], and the official guides contain no such sentence [2]
- A 19-clip probe found speaker IDs control voice, not lip placement; a combined rewrite that included the closed-lip sentence fixed 3 of 3 runs, and moving the non-speaker out of frame or turning them away fixed 12 of 12; the source separately calls the closed-lip sentence key [29]
- A community reference advises against prescribing a closed-mouth pose at all, which conflicts with the probe (unconfirmed) [30]
- H3 generates audio whether or not the prompt describes it, so an omitted field is a guess rather than silence [23]
- For a silent shot: no speaker ID, no `<d>`, a non-verbal soundscape, and the closed-lip sentence only if the mouth still moves [2][9][29]

## 5. Simple recipe

The recipe is one anchor sentence, two or three short clauses and no beat list; it is a proposal, and four of the ten live stems have a 1024x768 render: motion per second against the same-stem 5 s clip is IMG_8716 1.19x, IMG_7667 1.24x, IMG_8779 0.33x and IMG_8564 0.19x (near-duplicate 0.9967, plateau 8.3 s), so the other six stems are unrendered (unconfirmed).

- Alignment line first, then the three labelled fields [2]
- Sentence one: name the person and the scene as the picture shows them; one sentence, not a re-description [2][25]
- Clause one: one primary action with a visible start and a clear end [20][12]
- Clause two: one camera statement, `Static Shot` or one move with `at slow speed` or `at fast speed` [2]
- Clause three: one clause for what must hold [12]
- No timed beat list: timed segments are a community format that conflicts with the official continuous path, and the model cannot count (unconfirmed) [15][23][2]
- The smile stays exactly as in the photo; only its shape does not change: lip wording is what the sources use to steer the mouth [2][29]; no source shows that expression wording leaves the mouth still (unconfirmed)
- Positive wording only; no ban list [9]
- Audio: fill both fields explicitly; `overall_soundscape` carries room tone and action sound, `non_diegetic_music` is `N/A` when the clip should have no score [2][9]
- Ten seconds: describe one action that lasts the clip at normal speed [3]
- A short prompt is supported: structure matters more than wording [11], and a community count of official examples gives a median near 130 characters (unconfirmed) [32]

Generic example, person only:

```
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] A person sits at a wooden table in a quiet room, in the same clothes and posture as the picture. The person turns their head slowly toward the window and stops at the end of the clip. The camera holds a static shot. Their hands rest on the table and the background stays still.

overall_soundscape: Quiet room tone with a faint draught.

non_diegetic_music: N/A
```

## 6. Sources

1. MiniMax H3 model card - https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/README.md - 2026-08, revision 42ed227
2. MiniMax H3 base prompt guide - https://huggingface.co/MiniMaxAI/MiniMax-H3/blob/main/docs/VIDEO_PROMPT_WRITING_GUIDE_base_en.md - 2026-08, commit 5d9b308
3. MiniMax-AI H3 prompt-writing skill - https://github.com/MiniMax-AI/MiniMax-H3/blob/main/skills/h3-prompt-writing/SKILL.md - undated, fetched 2026-10-26
4. MiniMax video-generation API guide - https://platform.minimax.io/docs/guides/video-generation - undated, fetched 2026-10-26
5. MiniMax local deployment guide - https://platform.minimax.io/docs/guides/local-deploy-h3 - 2026-08-26
6. ComfyUI H3 nodes code - https://github.com/Comfy-Org/ComfyUI/blob/master/comfy_extras/nodes_minimax_h3.py - 2026-09-22, fetched 2026-10-26
7. ComfyUI H3 native tutorial - https://docs.comfy.org/tutorials/video/minimax/minimax-h3-native - undated, fetched 2026-10-26
8. ComfyUI H3 model page - https://docs.comfy.org/tutorials/video/minimax/minimax-h3 - undated, fetched 2026-10-26
9. ComfyUI H3 prompt guide - https://docs.comfy.org/tutorials/video/minimax/minimax-h3-prompt-guide - 2026-10-18, last commit
10. SGLang PR 36320 - https://github.com/sgl-project/sglang/pull/36320 - 2026-08-25, merged 2026-09-04
11. HF discussion 71 - https://huggingface.co/MiniMaxAI/MiniMax-H3/discussions/71 - 2026-08-11
12. HF discussion 65 - https://huggingface.co/MiniMaxAI/MiniMax-H3/discussions/65 - 2026-09-15
13. HF discussion 54 - https://huggingface.co/MiniMaxAI/MiniMax-H3/discussions/54 - 2026-08-06/07
14. HF discussion 108 - https://huggingface.co/MiniMaxAI/MiniMax-H3/discussions/108 - 2026-09-20
15. HF discussion 28 - https://huggingface.co/MiniMaxAI/MiniMax-H3/discussions/28 - 2026-08-03 to 2026-08-09
16. NegPiP node - https://github.com/hako-mikan/comfyui-minimax-h3-negpip - 2026-09-07
17. H3 Shadow Negative Nodes - https://huggingface.co/CCP6/H3-Shadow-Negative-Nodes - 2026-08-13
18. ai-primer local prompt control tests - https://www.ai-primer.com/creative/stories/minimax-h3-local-prompt-control-tests - 2026-09-29
19. siray.ai motion control guide - https://blog.siray.ai/minimax-h3-prompt-guide-motion-control/ - 2026-08-17
20. minimaxh3.tv prompt guide - https://minimaxh3.tv/blog/minimax-h3-prompt-guide - 2026-08-04
21. movey.ai local video lab - https://movey.ai/en/articles/minimax-h3-local-video-lab - 2026-08-12, updated 2026-08-17
22. sammcj H3 prompt reference - https://github.com/sammcj/agentic-coding/blob/main/Skills/llm-prompting-guide/references/minimax-h3.md - 2026-08-19
23. teskor-hub portable prompt - https://raw.githubusercontent.com/teskor-hub/minimax-h3-skill/main/portable-prompt.md - undated, accessed 2026-10-26
24. ai-primer local control tests - https://www.ai-primer.com/creative/stories/minimax-h3-local-control-tests - 2026-09-24
25. fuser.studio prompt guide - https://fuser.studio/articles/minimax-h3-prompt-guide - 2026-09-28
26. localai-org vllm.cpp commit - https://github.com/localai-org/vllm.cpp/commit/034493700902afe26640e573b65936bff213a188 - 2026-08-07
27. pttweb forum thread - https://www.pttweb.cc/bbs/AI_Art/M.1787143836.A.776 - 2026-08-19/20
28. Prodia H3 docs - https://docs.prodia.com/job-types/inference-minimax-h3-chili-txt2vid-v0/ - undated, accessed 2026-10-26
29. zenstory-ai drama-skills commit - https://github.com/zenstory-ai/drama-skills/commit/86c2aa1bb163207ecb75d14fb29a88cce24c78e0 - 2026-09-15
30. Cicaba native-audio reference - https://github.com/Cicaba/minimax-h3-prompts/blob/main/references/native-audio.md - 2026-08-17
31. minimax-h3.com dialogue guide - https://minimax-h3.com/blog/minimax-h3-dialogue-guide - 2026-09-17
32. orcarouter H3 guide - https://www.orcarouter.ai/blog/how-to-use-minimax-h3 - 2026-08-05
33. minimax3.com FL2VA guide - https://minimax3.com/blog/minimax-h3-first-last-frame - 2026-08-20

<!-- complete -->
