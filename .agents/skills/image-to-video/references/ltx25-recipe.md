# LTX-2.5 recipe

LTX-2.5 is the alternative to H3. A single 10 s pass settles into near-stillness, so the working method is a chain of two 121-frame natives.

## Model

- Repository `Lightricks/LTX-2.5`, revision `49b093a39c19169a8a81721dcc541e07e945232f`
- Weights `ltx-2.5-22b-dev-transformer-bf16`, `gemma4-12b-with-proj-ltx-2.5-bf16`, `ltx-2.5-video-vae-bf16`, `ltx-2.5-audio-vae-bf16`
- GPU `GPU-a44e514a-aa5b-2844-35f1-4be28e1921e5`, nvidia-smi index 1, RTX PRO 6000 96 GB
- Port 8190
- Setup `tmp/workflows/image-to-video/setup-chosen.json`
- GPU 2 variant `tmp/workflows/ltx25-preview/setup-ltx25-gpu2.json`, port 8193

## Values

- `PROMPT`, `NEGATIVE_PROMPT`, `SEED` 42, `WIDTH` 1024, `HEIGHT` 768 for the 4:3 chain, `LENGTH` 121 per chained part
- A portrait photo swaps width and height, but `render_ltx_chain_10s.py:57` hardcodes 1024, 768, 121 and 42 and reads no width or height, so change those constants
- LENGTH 241 (8k+1) is one 10.00 s native
- 121 per part is the chain length

## Settings

`MODEL_SETTINGS` is recorded in every sidecar:

```python
MODEL_SETTINGS = {
    "weights": "ltx-2.5-22b-dev-transformer-bf16, gemma4-12b-with-proj-ltx-2.5-bf16, ltx-2.5-video-vae-bf16, ltx-2.5-audio-vae-bf16",
    "steps": 30,
    "sampler": "euler",
    "scheduler": "LTXVScheduler max_shift 2.05 base_shift 0.95 stretch terminal 0.1",
    "cfg_video": 3.0,
    "cfg_audio": 7.0,
    "stg_scale": 1.0,
    "stg_blocks": "28",
    "modality_scale": 3.0,
    "image_strength": 1.0,
}
```

## Prompt composition

- Positive prompt: `GENERIC_SENTENCE` from `render-settings.json` plus the stem's `prompt_second_part` from `tmp/workflows/ltx25-preview/prompts/user/<stem>.json`, else `<stem>-6s.json` in the same folder (`render_ltx_chain_10s.py:89-90`, resolved by `prompt_source.py`)
- Negative prompt: `references/ltx-negative-prompt.txt` holds 1163 characters, 1164 bytes with the trailing newline
- The chain joins it with `, ` to each stem's 207-character `negative_extra` from `<stem>-ltx.json` in `tmp/workflows/ltx25-preview/prompts/`, so the rendered negative prompt is 1372 characters
- Only `negative_extra` is read from `<stem>-ltx.json`
- Its `prompt_second_part` is superseded
- Caveat: the chain reads `settings["NEGATIVE_PROMPT"]` from `render-settings.json` (`render_ltx_chain_10s.py:91`), byte-identical to the reference file today, so editing only the reference changes no render

## Chain method

- Render part A at 121 frames from the photo
- Extract its last frame, frame 120
- Render part B from that frame
- Concat A and B with the concat demuxer into 242 frames at 24 fps
- Interpolate to 300 at 30 fps
- The join is clean: motion_per_second 38.62 against 9.14 single-pass, near-duplicate frames 15.4% against 86.3%, join frame-difference ratio 1.10
- Sidecar: name the method, both part durations, the join frame and the steps

## Performance

- VRAM 75.7 GB on the 96 GB card
- The single-pass 10 s render peaked 79.0 GB
- About 20 min per clip (2 x about 10)

## Known failure

- A single pass at LENGTH 241 settles against 29.0 at 5 s
- At 30 steps it measures motion_per_second 9.14
- At 60 steps it measures motion_per_second 9.60
- Steps are not the lever
- Fix: chain two 121-frame natives
- Raising steps does not help
- The chain failed the hand-action rule: the crayon mark missed the crayon tip
- H3 followed it
