# Release

Checklist for every commit and push to the repository. Commit, push, tag and version bump each need the Star Colonel's approval.

- [ ] Hooks enabled - `pre-commit` checks the staged files and `pre-push` checks every file of the commits being pushed, so a `--no-verify` commit cannot reach a remote; both run `.githooks/photo_guard.py`: `git config core.hooksPath .githooks` (once per clone)
- [ ] Notebook outputs cleared: `find notebooks -name '*.ipynb' -not -path '*/.ipynb_checkpoints/*' -exec .venv/bin/jupyter nbconvert --clear-output --inplace {} +`
- [ ] No photo, clip or model weight staged - the commit hook refuses non-`.md` files under `data/`, byte copies of `data/raw/` and `data/external/` originals, image or video bytes outside `.images_readme/`, `.images_readme/` images without a `<stem>.md` sidecar and notebook attachments, and admits only the three owner showcase files under `data/external/showcase/` listed by sha256 and path in `.githooks/showcase.sha256`; check weights by eye: `git diff --cached --name-only`
- [ ] `make lint` and `make test` pass
- [ ] Journal entry added through `/journal:update`
- [ ] Conventional commit message, no attribution trailer
