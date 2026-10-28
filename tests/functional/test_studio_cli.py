"""The real ``henryk-media studio`` console script: it serves the page and exits 0 on SIGINT."""

import os
from pathlib import Path
import signal
import socket
import subprocess
import time
import urllib.request

from henryk_media.config import PROJ_ROOT


def test_cli_serves_and_exits_zero_on_sigint(image_tree: Path, tmp_path: Path) -> None:
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    command = [
        str(PROJ_ROOT / ".venv/bin/henryk-media"),
        "studio",
        "--port",
        str(port),
        "--state-dir",
        str(tmp_path / "state"),
        "--input-root",
        str(image_tree / "data/raw"),
    ]
    env = {**os.environ, "JUPYTERHUB_SERVICE_PREFIX": "/user/test/"}
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env
    )
    try:
        deadline = time.monotonic() + 60
        while True:  # GET / only: no nvidia-smi and no ComfyUI
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{port}/", timeout=5) as response:
                    status, page = response.status, response.read()
                break
            except OSError:
                assert process.poll() is None, process.communicate()[0]
                assert time.monotonic() < deadline, "the studio did not answer within 60 s"
                time.sleep(0.2)
        assert status == 200
        assert b"<title>Henryk studio</title>" in page
        process.send_signal(signal.SIGINT)
        output, _ = process.communicate(timeout=30)
        assert process.returncode == 0, output
        assert f"local URL: http://127.0.0.1:{port}/" in output
        assert f"proxy URL: /user/test/proxy/{port}/" in output
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
