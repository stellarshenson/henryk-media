"""Tests for the ``henryk-media studio`` command: URLs, loopback guards and a taken port."""

from http.server import ThreadingHTTPServer
from pathlib import Path
import socket

import pytest
from typer.testing import CliRunner

from henryk_media.studio.cli import app
from henryk_media.studio.comfy import comfy_setup


def run_studio(tmp_path: Path, *options: str):
    """Invoke the command with a temporary state folder and input root."""
    (tmp_path / "roots").mkdir(exist_ok=True)
    arguments = ["studio", "--state-dir", str(tmp_path / "state")]
    return CliRunner().invoke(app, [*arguments, "--input-root", str(tmp_path / "roots"), *options])


def test_studio_prints_the_local_and_proxy_urls(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def interrupted(self: ThreadingHTTPServer) -> None:
        raise KeyboardInterrupt

    monkeypatch.setattr(ThreadingHTTPServer, "serve_forever", interrupted)
    monkeypatch.setenv("JUPYTERHUB_SERVICE_PREFIX", "/user/lab")
    result = run_studio(tmp_path, "--port", "0")
    assert result.exit_code == 0, result.output
    port = int(result.output.split("local URL: http://127.0.0.1:")[1].split("/")[0])
    assert f"local URL: http://127.0.0.1:{port}/" in result.output
    assert f"proxy URL: /user/lab/proxy/{port}/" in result.output


def test_studio_and_comfyui_listen_on_loopback_only(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    for host in ("0.0.0.0", "192.168.1.10", "::1", "localhost"):
        result = run_studio(tmp_path, "--host", host)
        assert result.exit_code == 2, (host, result.output)
        assert "loopback" in result.output

    addresses = []

    def interrupted(self: ThreadingHTTPServer) -> None:
        addresses.append(self.server_address)
        raise KeyboardInterrupt

    monkeypatch.setattr(ThreadingHTTPServer, "serve_forever", interrupted)
    assert run_studio(tmp_path, "--port", "0").exit_code == 0
    assert addresses[0][0] == "127.0.0.1"

    words = comfy_setup("GPU-test", 8600).launch_command.split()
    assert words.count("--listen") == 1
    assert words[words.index("--listen") + 1] == "127.0.0.1"


def test_state_dir_under_data_is_refused(tmp_path: Path) -> None:
    from henryk_media.config import DATA_DIR

    result = CliRunner().invoke(app, ["studio", "--state-dir", str(DATA_DIR / "studio")])
    assert result.exit_code == 2
    assert not (DATA_DIR / "studio").exists()


def test_port_in_use_exits_non_zero_naming_the_port(tmp_path: Path) -> None:
    with socket.socket() as taken:
        taken.bind(("127.0.0.1", 0))
        taken.listen()
        port = taken.getsockname()[1]
        result = run_studio(tmp_path, "--port", str(port))
    assert result.exit_code != 0
    assert f"port {port} is already in use" in result.output
    assert not (tmp_path / "state").exists()  # refused before the studio touched its folder
