<!-- @import /home/lab/workspace/.claude/CLAUDE.md -->

# Project-Specific Configuration

This file imports workspace-level configuration from `/home/lab/workspace/.claude/CLAUDE.md`.
All workspace rules apply. Project-specific rules below strengthen or extend them.

The workspace `/home/lab/workspace/.claude/` directory contains additional instruction files
(MERMAID.md, NOTEBOOK.md, DATASCIENCE.md, GIT.md, and others) referenced by CLAUDE.md.
Consult workspace CLAUDE.md and the .claude directory to discover all applicable standards.

## Mandatory Bans (Reinforced)

The following workspace rules are STRICTLY ENFORCED for this project:

- **No automatic git tags** - only create tags when user explicitly requests
- **No automatic version changes** - only modify version in package.json/pyproject.toml/etc. when user explicitly requests
- **No automatic publishing** - never run `make publish`, `npm publish`, `twine upload`, or similar without explicit user request
- **No manual package installs if Makefile exists** - use `make install` or equivalent Makefile targets, not direct `pip install`/`uv install`/`npm install`
- **No automatic git commits or pushes** - only when user explicitly requests

## Project Context

**henryk-media** - AI generation and manipulation of media for Henry (Henryk), the Star Colonel's
son. The first use case is animating still photos into short video clips (image-to-video); other
derived media follow as requested.

**Technology Stack**:
- copier-data-science template v1.3.21 (`.copier-answers.yml`), Python 3.13, uv environment at `.venv`
- `make install` / `make test` / `make lint` / `make format` drive the environment and checks
- ruff for linting and formatting, pytest for tests
- Data and model sync to S3 bucket `general-purpose/henryk-media`, AWS profile `stellars-tech`

**Directory Layout**:
- `data/raw/` - original photos and videos of Henry, immutable, gitignored
- `data/processed/` - generated media of approved production runs, gitignored
- `tmp/media/` - bench and test renders, gitignored
- `models/` - third-party model weights move through `make sync_models_*`, never git
- `notebooks/` - generation experiments, numbered in execution order per task folder
- `src/henryk_media/` - stable code graduated from notebooks

## Journal Rules (Project-Specific)

- **APPEND ONLY**: New journal entries MUST be appended at the end of the file, never inserted between existing entries
- Entries maintain strict chronological order by position - the last entry in the file is always the most recent work
- Never reorder, move, or insert entries out of sequence
- The Stellars **journal plugin** is the canonical tool for this file: create via `/journal:create`, append via `/journal:update`, archive via `/journal:archive`. The `journal:journal` skill auto-triggers on any mention of "journal" and runs `journal-tools check` after every write
- Direct edits to `JOURNAL.md` are a last resort - prefer the plugin so modus secundis format, continuous numbering and append-only order are enforced automatically

## Strengthened Rules

- **Privacy of a minor** - photos and videos of Henry are personal data of a child. Never send them to an external service (cloud generation API, web tool, browser upload) without the Star Colonel's explicit approval for that service. Prefer models that run locally on the workstation GPUs
- **Originals are immutable** - never modify, overwrite or delete files in `data/raw/`; every generated file goes to a different directory
- **Only production runs write to data** - a bench or test render writes under `tmp/media/<subfolder>/`, never into `data/`. `data/interim/` and `data/processed/` receive only outputs of an approved production run, each with its `.md` sidecar, and `tmp/` is gitignored so bench media never reaches git
- **Human review gates promotion** - a generated image or clip reaches `data/processed/` only after the Star Colonel has viewed it and judged it good, or when he declares the run production before viewing it. Agents render, measure and present candidates with their paths; the promotion follows his verdict, never an agent's own.
- **Generated media stays distinguishable from originals** - every output gets a `.md` sidecar naming the source file, the model, the prompt and the settings, so no generated clip can be mistaken for a genuine recording
- **GPU work** sets `CUDA_VISIBLE_DEVICES` to the nvidia-smi index before importing torch; the `my-gpu` skill carries the device inventory and inference recipes
- **Experiments live in notebooks**, not in `/tmp` scripts; long generation runs execute detached and log to `logs/<name>.log`
- **Only the latest render** - a new render of a model first moves that model's previous clips and sidecars to the trash, so its output folder and its notebook hold only the latest render
- **No child images in notebooks** - a notebook never stores image or video data of a child. Photos and clips are shown only by link (`IPython.display.Image(url=<relative path>)`, `Video(<relative path>, embed=False)`), never embedded as base64 or through `Image(filename=...)`
- **Notebooks reach the repository without outputs** - every notebook is committed and pushed with all outputs and execution counts cleared; `RELEASE.md` in the repository root is the checklist for every commit and push
