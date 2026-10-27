# Prompt recipes

The H3 prompt grammar, the simple recipe and the measured speech and motion results behind the prompt and fault rules in `SKILL.md`. LTX-2.5 keeps its two-part prompt in `ltx25-recipe.md`.

## H3 grammar

The prompt is the alignment line, one blank line, then the three labelled fields in this order.

```
For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) is fully referenced.

integrated_multimodal_description: [Shot 1] <the scene as the photo shows it>; <one action with a visible start and a clear end>; <one camera statement>; <one hold clause>

overall_soundscape: <non-verbal room tone and action sound>

non_diegetic_music: N/A
```

- The alignment line is exact, including `<Picture 1>` and `[Shot 1]`
- `integrated_multimodal_description` opens with `[Shot 1]`, names the person and scene as the photo shows them, and carries one primary action with a visible start and a clear end
- One camera statement: `Static Shot`, or one move with a speed such as `at slow speed`
- One hold clause names the hands, props, background people and cut edges as the photo shows them, in positive words
- The photo's expression stays fixed: the same smile, lips and teeth, and the smile does not change shape
- No timed beat list: the first-two-seconds, by-four-seconds form is a community format, not the official grammar
- `overall_soundscape` is one to four sentences of non-verbal room tone and action sound
- `non_diegetic_music` is `N/A` when the clip needs no score
- Fill both even for a silent clip
- No speaker ID, no `<d>` and no speech word: they request dialogue
- An omitted audio field is a guess rather than silence
- H3 has no negative prompt
- H3 has no adjustable CFG: the checkpoint is CFG-distilled and the graph runs one BasicGuider at cfg 1 with positive conditioning only
- Add no negative prompt, no ban list and no CFG value
- Sources and the full guide: `docs/model-selection/minimax-h3-prompting.md`

## Simple recipe

- One alignment line, three fields, one action, one camera statement and one hold clause
- Keep it short: structure matters more than wording

## Speech results

Explicit mouth-stillness wording is the strongest measured lever, stronger in Chinese than in English. On IMG_7667 no tested wording eliminated the mouth motion at 1024x768; the best was 0.56 of the control.

Conditions: 2026-10-27, 1024x768, 10 s, seed 42, one render per variant. Baseline: LivePortrait clip tmp/media/liveportrait/IMG_7666.mp4, native 30 fps. The 480x320 screen ratios are not resolution-comparable.

| Variant | Mouth score | Ratio to control 5.7885 | Ratio to LivePortrait baseline 2.5043 |
| --- | ---: | ---: | ---: |
| S5 | 3.5648 | 0.62x | 1.42x |
| S7 T1 | 4.2228 | 0.73x | - |
| S7 T2 | 3.2561 | 0.56x | 1.30x |

- S5 screened 0.02x at 480x320, while the same prompt gives the 3.5648 score at 1024x768
- The CFG negative S4 measured 0.73 of the control at 480x320
- Sound design alone S2 measured 0.19
- The T2 package with a very slight tilt, T3, measured 1.10 of the control, so the tilt made the mouth worse

## Motion results

Motion per second is measured against the same-stem 5 s clip at 25.6787.

| Variant | Motion per second | Ratio |
| --- | ---: | ---: |
| M1 | 20.46 | 0.80x |
| M2 | 16.84 | 0.66x |
| M3 | 33.08 | 1.29x |

IMG_8716 paired motion at 1024x768:

| Variant | Motion per second | Near-duplicate |
| --- | ---: | ---: |
| R1, an eased head tilt | 9.74 | 0.836 |
| R2, a slight gift-bag lift plus a tilt | 12.84 | 0.656 |
| Simple control | 7.39 | 0.903 |
| Delivered clip | 7.03 | 0.9532 |

## Resolution caveat

- The same M0 prompt moved 23.79 at 480x320 against 4.98 at 1024x768
- A small render screens only and never judges motion

## Mouth-screen caveat

- The mouth screen is a 64x64 grayscale lower-face difference over 38 of 299 pairs
- It is a heuristic that follows head motion, not a speech detector
- The Star Colonel judges speech by viewing
