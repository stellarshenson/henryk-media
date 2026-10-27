# Client API

`src/henryk_media/animation/image_to_video.py` starts one ComfyUI server per setup, renders a working copy through the model's graph, interpolates the native clip to 300 frames at 30 fps with FILM, records wall time and peak VRAM, and stops the server. A finished clip whose checkpoint matches is restored instead of rendered again.

## Setup

- `Setup.load(path)` reads a setup JSON: `model`, `revision`, `gpu` (nvidia-smi UUID), `port`, `native_fps`, `launch_command`, `stop_command`, `io_dirs`, `workflow_api_path`
- `revision` falls back to the setup's `repository` string when the setup records no separate revision
- `gpu` keeps only the UUID, the first whitespace-separated token
- `io_dirs` holds the server's input, output and temp folders
- `workflow_api_path` is the graph
- The notebook only loads the setup
- `Server(setup)` runs its `launch_command`, waits up to three minutes for `/system_stats`, and stops the server at exit

## Server

- `Server(setup)` refuses a busy port and a missing FILM weight (`make comfyui_frame_interpolation` provides it)
- `Server.stop()` runs the setup's `stop_command` and waits for the port to close
- `Server.run(graph)` submits `/prompt`, waits for the history entry, and returns the entry, wall seconds and peak GPU MiB
- `Server.free_gpu()` unloads the server's models and waits for 6144 MiB free before interpolation

## Render

- `Server.render(source, clip, variant, values, settings)` fills each marker in `values`, sets `{{IMAGE}}` and `{{FILENAME_PREFIX}}`, submits `/prompt`, moves the mp4 to temp, checks native rate and length, frees the GPU, interpolates, and writes `<clip>.md` and `checkpoints/<clip stem>.json`
- `render` rejects a 121-frame part as too short for 300 frames
- A chain submits each part through `Server.run` and interpolates the join with `i2v.interpolate(join, clip, setup.gpu)`
- `render` restores a finished clip only when model, revision, settings and the source fingerprint match and the clip probes as 300 frames at 30 fps
- Any other clip is rendered again
- The native clip must last at least (FRAMES-1)/FPS = 9.97 s or `render` raises

## Values

- Markers `{{PROMPT}}`, `{{WIDTH}}`, `{{HEIGHT}}`, `{{LENGTH}}`, `{{SEED}}`
- `{{NEGATIVE_PROMPT}}` is used on LTX-2.5
- `{{IMAGE}}` and `{{FILENAME_PREFIX}}` are set by the module

```python
from henryk_media.animation import image_to_video as i2v
prompt = f"{ALIGNMENT}\n\n{description}\n\n{soundscape}\n\n{music}"  # one line, blank line, three fields
server = i2v.Server(i2v.Setup.load(SETUP_FILE))
values = {"{{PROMPT}}": prompt, "{{WIDTH}}": 1024, "{{HEIGHT}}": 768,
          "{{LENGTH}}": 243, "{{SEED}}": 42}
result = server.render(source, clip, "production-4x3", values, SETTINGS)
server.stop()
```

## Interpolation

- `i2v.interpolate(native, clip, gpu)` runs `frame_interpolation.py` in ComfyUI's environment with `film_net_fp16.safetensors`, writing 300 frames at 30 fps
- `FRAMES` is 300
- `FPS` is 30

## Sidecar

- `<clip>.md` records the source, model, revision, variant, settings, GPU, seconds, peak VRAM and probe values
- `checkpoints/<clip stem>.json` holds the same result and is the restore key
- Graph values are recorded under the lowercase marker name without braces, so `{{NEGATIVE_PROMPT}}` becomes `negative_prompt`
- The sidecar's `prompt=` is the source of what was rendered
- For a chain, the `Part A prompt:` and `Part B prompt:` lines are what each part received
