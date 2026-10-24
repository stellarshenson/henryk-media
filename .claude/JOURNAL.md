# Claude Code Journal

This journal tracks substantive work on documents, diagrams, and documentation content.

---

1. **Task - Project initialization** (v0.1.0): Set up agent instructions and documentation for the AI media project for Henry<br>
   **Result**: The project started as an uncommitted copier-data-science v1.3.21 scaffold with no agent configuration. Created `.agents/AGENTS.md` from the init template with the mandatory bans, the journal rules, the project context (image-to-video animation of still photos as the first use case, uv and Makefile stack, S3 sync to `general-purpose/henryk-media`) and strengthened rules for privacy of a minor, immutable originals in `data/raw/`, `.md` provenance sidecars for every generated file, GPU device selection and notebook-based experiments. Created `.agents/skills/` and `.agents/workflows/` with `.gitkeep` and linked `.claude/CLAUDE.md`, `.claude/skills` and `.claude/commands` to them. Added the project purpose and data-handling rules to `README.md`. Created private NAS GitLab project `konrad.jelen/henryk-media` (id 85) as `origin`, same namespace as the other henryk repos.
