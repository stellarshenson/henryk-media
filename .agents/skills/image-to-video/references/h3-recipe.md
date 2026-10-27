# H3 recipe

MiniMax H3 renders the whole 10 s clip in one native pass on GPU 2. Every value and setting below is recorded in the clip's sidecar.

## Model

- Repository `Comfy-Org/MiniMax-H3`, revision `e5eb578a89295337b8ff433a035929ce0279e0b6`
- Weights `minimax_h3_fl2va_pruned_bf16.safetensors`, `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors`, `minimax_h3_video_vae_fp16.safetensors`, `minimax_h3_audio_vae_fp32.safetensors`
- GPU `GPU-1223ff00-ce71-874f-592e-a4429e9f47ba`, nvidia-smi index 2, RTX PRO 5000 72 GB
- Port 8192
- Setup `tmp/workflows/image-to-video/setup-minimax.json`

## Values

- `PROMPT`, `WIDTH`, `HEIGHT`, `LENGTH` 243, `SEED` 42
- LENGTH 243 is 17k+5: 242 native frames at 24 fps, 242/24 = 10.08 s, interpolated to 300 at 30 fps
- No `{{NEGATIVE_PROMPT}}`: the checkpoint is CFG-distilled and the graph has one BasicGuider with positive conditioning only

## Settings

`SETTINGS` is recorded in every sidecar:

```python
SETTINGS = {
    "steps": 20,
    "sampler": "res_multistep",
    "scheduler": "simple",
    "shift": "12 video, 3 audio (MiniMaxH3 model settings)",
    "cfg": "none: CFG-distilled checkpoint, BasicGuider with positive conditioning only",
    "negative_prompt": "camera movement, zoom, changing face, morphing, distorted hands, extra fingers, text",
    "negative_prompt_applied": "no: the graph has no negative conditioning input",
    "weights": "minimax_h3_fl2va_pruned_bf16.safetensors, qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors, minimax_h3_video_vae_fp16.safetensors, minimax_h3_audio_vae_fp32.safetensors",
}
```

- The `negative_prompt` string is recorded but `negative_prompt_applied` is `no`, so the string changes no render

## Performance

- VRAM 64.4 to 69.5 GB
- About 21 to 24 min per clip
- One pass covers the whole 10 s
- No chain
