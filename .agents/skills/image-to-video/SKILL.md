---
name: image-to-video
description: Animates a photo into a 10 second clip with MiniMax H3 or LTX-2.5 from an extended frame. Use when asked to animate, enliven, render or re-render a photo into a clip, to fix motion in a clip, or when MiniMax H3, LTX-2.5 or the image-to-video notebooks are named.
---

# Image-to-video

A whole-frame model redraws and animates the extended frame from a prompt.

## Sequence

- Extend the frame first, so the model animates a finished frame, not an invented scene
- 1024x768 for a 4:3 frame, 768x1024 for a portrait
- Native 24 fps
- Target 300 frames at 30 fps, 10.00 s (`frame_interpolation.py`, `film_net_fp16.safetensors`)
- H3 covers the whole 10 s in one native pass
- LTX-2.5 settles into near-stillness, so chain two 121-frame natives
- The native clip must last at least (FRAMES-1)/FPS seconds, 9.97 s here, or `render` raises
- A chain joins 242 native frames at 24 fps, so it clears the same check
- The delivered mp4 has no audio stream: the H3 graph generates audio jointly, but the interpolation writes video only
- One renderer per GPU port
- A clip whose checkpoint matches model, revision and settings is restored, not re-rendered
- Model choice: H3 in `references/h3-recipe.md`
- Model choice: LTX-2.5 in `references/ltx25-recipe.md`
- Client, values and sidecar: `references/client-api.md`

## Prompt

The official grammar is H3-only; LTX-2.5 keeps its two-part prompt.

- The prompt is the alignment line, one blank line, then `integrated_multimodal_description`, `overall_soundscape` and `non_diegetic_music` in that order
- The alignment line is exact, including `<Picture 1>` and `[Shot 1]`
- One action with a visible start and a clear end
- One camera statement: `Static Shot` or one move with a speed such as `at slow speed`
- One positive hold clause naming the hands, props, background people and cut edges
- The photo's expression stays fixed: the same smile, lips and teeth, and the smile does not change shape
- No speaker ID, no `<d>` and no speech word
- Fill both audio fields even for a silent clip
- `non_diegetic_music` is `N/A` when no score
- H3 has no negative prompt
- H3 has no adjustable CFG: the checkpoint is CFG-distilled, one BasicGuider at cfg 1 with positive conditioning only
- Full grammar, simple recipe and measured results: `references/prompt-recipes.md`

## Faults

- Stranger or face at the cut edge: the hold clause names the background people and cut edges as the photo shows them
- Background person redrawn forward or larger: describe them as unchanged, same size and place
- Hand action with no visible result: name the mark and its place
- Slow motion or a still clip: state one action with a visible start and a clear end at normal speed
- No timed beats
- Sudden head tilt or jumpy motion: keep movement slow, smooth and gradual
- Movement is not excessive
- A head turn eases in and out over two to three seconds
- Amplitude small
- An open grin read as speech: fill both audio fields
- An open grin read as speech: write no speaker ID, no `<d>` and no speech word
- An open grin read as speech: then add explicit mouth-stillness wording
- The measured levers are in `references/prompt-recipes.md`
- LTX single pass near-still: chain two 121-frame natives
- Raising steps does not help (`references/ltx25-recipe.md`)
- Read the recorded prompt first: the sidecar's `prompt=` is the source
- For a chain, the `Part A prompt:` and `Part B prompt:` lines are what each part received (`references/client-api.md`)

<!-- improved 2026-10-25 | body 603→578w / 60→60L | benchmark n/a (not-requested) | via improve-skill -->
<!-- improved 2026-10-25 | body 582→395w / 60→45L | benchmark n/a (not-requested) | via improve-skill -->
<!-- filled 2026-10-25 | body 395→788w / 45→101L | benchmark n/a (not-requested) | via skill-fill -->
<!-- fixed 2026-10-25 | body 788→852w / 101→102L | benchmark n/a (not-requested) | via speech-rootcause -->
<!-- fixed 2026-10-25 | body 852→888w / 102→103L | benchmark n/a (not-requested) | via skill-6s -->
<!-- fixed 2026-10-26 | body 888→1152w / 103→93L | benchmark n/a (not-requested) | via skill-10s -->
<!-- fixed 2026-10-26 | body 1138→1161w / 94→94L | benchmark n/a (not-requested) | via fix2-skill -->
<!-- fixed 2026-10-26 | body 1161→1233w / 94→104L | benchmark n/a (not-requested) | via skill-h3-grammar -->
<!-- fixed 2026-10-27 | body 1433→1569w / 107→107L | measured IMG_8716 R1/R2 and the speech conclusion -->
<!-- improved 2026-10-27 | body 1569→538w / 107→49L | benchmark n/a (not-requested) | via improve-skill -->
