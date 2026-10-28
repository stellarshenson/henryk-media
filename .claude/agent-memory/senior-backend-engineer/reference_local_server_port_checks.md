---
name: local-server-port-checks
description: On this WSL2 workstation ss reports no TCP listeners at all, so check local HTTP servers with curl instead
metadata:
  type: reference
---

`ss -ltn` on this workstation returns an empty list even while a server answers on 127.0.0.1, for example ComfyUI on 8191 or JupyterLab on 8888.

**Why:** verified 2026-10-25 while stopping the Wan2.2 ComfyUI server; `ss -ltnp` and `ss -ltn` both showed zero lines, while `curl http://127.0.0.1:8191/system_stats` returned JSON.

**How to apply:** confirm a local server is up or down with `curl -s -m 3 <url>`, and confirm shutdown with `ps -p <pid>` plus a GPU memory reading. Do not treat an empty `ss` output as evidence that a port is closed.
