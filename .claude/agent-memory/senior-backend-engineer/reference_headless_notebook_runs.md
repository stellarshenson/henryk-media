---
name: headless-notebook-runs
description: nbconvert execution in henryk-media - project kernel name, rich Progress output lost, harmless IOPub timeout
metadata:
  type: reference
---

- Run `.venv/bin/jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.kernel_name=python3 <notebook>`; that kernel runs .venv/bin/python, while the notebook metadata keeps `venv-henryk-media-py`
- nbconvert prints `Timeout waiting for IOPub output` when a cell ends with a rich Progress display; the notebook is still written with no error output
- rich Progress saves as empty display_data (text/plain `Output()`), so per-item messages in that cell are not in the saved notebook; put measurements in a table and log the run detached
- `pgrep -f "nbconvert.*<name>"` matches the watching shell's own command line; capture `$!` and wait on that PID instead

Related: [[minimax-h3-render]]
