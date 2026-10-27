# henryk-media

Generation and manipulation of media for Henry, a child. The first campaign extends birthday photos
into landscape frames and animates each frame into a 10 second clip. Every model runs on the
workstation GPUs, and no photo or clip is sent to an external service.

## How it works

- Image outpainting extends a photo sideways into 4:3 at 1280 x 960 or 16:9 at 1280 x 720
- FLUX 3 Klein and its outpaint LoRA generate only the added side panels
- The photo's interior pixels are pasted back unchanged
- A person gate rejects a frame whose panels add a face or person, and the next seed is tried
- Image-to-video animates the extended frame into a 10 second clip with MiniMax H3 or LTX-2.5
- FILM interpolates the native frames to 30 fps, 300 frames per clip
- The models run through ComfyUI servers bound to `127.0.0.1`; nothing is sent to an external service

## Where the pieces live

- `notebooks/henryk-urodziny-2026/` - `01-kj-image-extender.ipynb` through
  `05-kj-minimax-h3.ipynb`, in execution order
- `src/henryk_media/imaging/` - extender, person gate, composite, provenance, registry and server
- `src/henryk_media/animation/` - image-to-video client, FILM interpolation, LivePortrait wrappers
- `.agents/skills/` - the `image-outpainting` and `image-to-video` working recipes
- `docs/model-selection/` - the research guides and decision records
- `docs/acc-crit.md` and `docs/defects.md` - the acceptance-criteria and defects trackers
- `data/external/henryk-urodziny-2026/prompts/` - the prompts that produced the campaign media

## Data and privacy

- Files in `data/raw/` are originals and are never modified, overwritten or deleted
- Only an approved production run writes `data/processed/` and `data/interim/`
- Every generated file gets a `.md` sidecar naming its source, model, prompt and settings
- A render reaches `data/processed/` only after the Star Colonel views it and judges it good, or declares the run production
- A bench or test render writes under `tmp/media/` and never into `data/`
- Notebooks link photos and clips by relative path and never embed them
- Notebooks are committed with outputs cleared; `RELEASE.md` is the checklist

## Setup

```bash
make install
```

- `make comfyui_environment` - Create the ComfyUI environment with CUDA 13.0 torch and the node pack requirements
- `make comfyui_frame_interpolation` - Download the FILM weights ComfyUI's core frame-interpolation nodes load to reach 30 fps

## Makefile targets

- `make install` - Create the uv environment and install the package
- `make test` - Run the pytest suite
- `make lint` / `make format` - Check / fix code style
- `make requirements` / `make upgrade` - Install / upgrade dependencies with uv
- `make create_environment` / `remove_environment` / `register_environment` - Manage the environment
- `make data` - Run `src/henryk_media/dataset.py`
- `make build` / `make clean` - Build the wheel / remove caches, logs and `tmp/`
- `make sync_data_down` / `sync_data_up` - Sync `data/` with the lab S3 endpoint
- `make sync_models_down` / `sync_models_up` - Sync `models/` with the lab S3 endpoint
- The sync targets use the `stellars-tech` profile and bucket `general-purpose/henryk-media`
- `make .env` / `make .env.enc` - Decrypt / encrypt the environment secrets
- `make help` - List every target with its description

## Project organization

```
├── .agents/skills/       <- image-outpainting and image-to-video recipes
├── data/
│   ├── external/         <- source photos, driving clips, prompt archive
│   ├── interim/          <- working copies
│   ├── processed/        <- approved frames and clips
│   └── raw/              <- originals, immutable
├── docs/
│   ├── model-selection/  <- research guides and decision records
│   ├── acc-crit.md       <- acceptance criteria tracker
│   ├── defects.md        <- defects tracker
│   └── video-scene-control.md
├── logs/                 <- background-job logs (gitignored)
├── models/
│   ├── photo-animation/  <- ComfyUI and weights (gitignored)
│   └── photo-animation.md <- how to recreate them
├── notebooks/henryk-urodziny-2026/
├── references/           <- external material
├── reports/              <- generated analysis and figures
├── src/henryk_media/
│   ├── animation/
│   └── imaging/
├── tests/
├── tmp/                  <- scratch and bench renders (gitignored)
├── Makefile, pyproject.toml
└── RELEASE.md            <- commit and push checklist
```

> **Note**: Generated with copier-data-science template v1.3.21
> For template documentation, visit [copier-data-science](https://github.com/stellarshenson/copier-data-science)

## Links

- [Release checklist](RELEASE.md), [acceptance criteria](docs/acc-crit.md), [defects](docs/defects.md)
- [Data rules](data/README.md), [models](models/README.md), [notebooks](notebooks/README.md),
  [references](references/README.md)
