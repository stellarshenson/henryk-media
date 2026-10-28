---
name: nas-model-store
description: /mnt/nas-shared/models behaviour - write speed, read-speed collapse, other sessions mutating the store, and how to verify large model sets there
metadata:
  type: reference
---

- `/mnt/nas-shared/models` is NFSv3 mounted `soft,timeo=50,retrans=2,rsize=wsize=1MiB` from 172.23.255.253; the standard layout is one folder per model named `<org>--<repo>` with a `<org>--<repo>.md` sidecar beside it
- Writes ran at about 50 MB/s on 2026-10-25, but reads collapsed the same morning to 0.3-3.3 MB/s (about 800 ms per 1 MiB read RPC against a 29 ms historical average). Older folders were equally slow and eight parallel readers gave no gain, so the cause was server side, not the client or the page cache
- The kernel logged repeated `NFS: server error: fileid changed` on the shared export, and another session removed several model folders from the store at 05:20 that morning. Re-list the store before assuming a folder is still there
- Verify a large set with a per-file resumable hasher (the `tmp/workflows/nas-llm/verify_model.py` pattern: stat, hash, checkpoint after every file). At 3 MB/s a 360 GB set needs about 30 hours, so never plan it as one foreground pass
- `hf download --local-dir` writes straight into the target folder, with bookkeeping under `<local-dir>/.cache/huggingface/`; `--max-workers 1` wrote 360 GB onto this share with no EIO and no local staging
- The workstation often runs several agent sessions at once (load average reached 91 on 64 cores); concurrent sessions share the NAS and its bandwidth
