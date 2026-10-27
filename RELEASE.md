# Release

Checklist for every commit and push to the repository. Commit, push, tag and version bump each need the Star Colonel's approval.

- [ ] Commit hook enabled - it fails a commit that stages a notebook with outputs: `git config core.hooksPath .githooks` (once per clone)
- [ ] Notebook outputs cleared: `find notebooks -name '*.ipynb' -not -path '*/.ipynb_checkpoints/*' -exec .venv/bin/jupyter nbconvert --clear-output --inplace {} +`
- [ ] No photo, clip or model weight staged - only `.md` files under `data/`: `git diff --cached --name-only`
- [ ] `make lint` and `make test` pass
- [ ] Journal entry added through `/journal:update`
- [ ] Conventional commit message, no attribution trailer
