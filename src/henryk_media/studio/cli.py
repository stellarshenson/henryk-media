"""The ``henryk-media`` console script; ``henryk-media studio`` serves the studio on loopback."""

import errno
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import ipaddress
import os
from pathlib import Path
from typing import Annotated

import typer

from henryk_media.config import DATA_DIR, PROJ_ROOT
from henryk_media.studio.app import Studio, default_roots
from henryk_media.studio.generators import Outpaint, Video
from henryk_media.studio.web import handler

STATE_DIR = PROJ_ROOT / "tmp" / "media" / "studio"

app = typer.Typer(add_completion=False, no_args_is_help=True)


@app.callback()
def main() -> None:
    """Henryk media tools."""  # without a callback typer runs the single command as the root


def proxy_url(port: int) -> str:
    """Return the studio URL as the JupyterLab proxy exposes it."""
    prefix = os.environ.get("JUPYTERHUB_SERVICE_PREFIX", "/")
    return f"{prefix if prefix.endswith('/') else prefix + '/'}proxy/{port}/"


@app.command()
def studio(
    host: Annotated[str, typer.Option(help="IPv4 loopback address to listen on.")] = "127.0.0.1",
    port: Annotated[int, typer.Option(help="Port to listen on.")] = 8520,
    state_dir: Annotated[
        Path, typer.Option(help="Folder for uploads, prompts and results; not under data/.")
    ] = STATE_DIR,
    input_root: Annotated[
        list[Path] | None,
        typer.Option(help="Folder the picker lists; repeatable. Default: the project data roots."),
    ] = None,
) -> None:
    """Serve the outpainting and MiniMax H3 studio on 127.0.0.1 until Ctrl+C."""
    try:
        loopback = ipaddress.IPv4Address(host).is_loopback
    except ValueError:
        loopback = False
    if not loopback:
        raise typer.BadParameter(f"{host} is not an IPv4 loopback address", param_hint="--host")
    if state_dir.resolve().is_relative_to(DATA_DIR.resolve()):
        raise typer.BadParameter(
            f"{state_dir} lies under {DATA_DIR}; the studio never writes there",
            param_hint="--state-dir",
        )
    try:
        server = ThreadingHTTPServer((host, port), BaseHTTPRequestHandler)
    except OSError as error:
        if error.errno != errno.EADDRINUSE:
            raise
        typer.echo(f"port {port} is already in use", err=True)
        raise typer.Exit(1) from error
    # bound before the studio starts, so a second instance never marks the first one's jobs
    studio = Studio(
        state_dir, input_root or default_roots(), {"outpaint": Outpaint(), "video": Video()}
    )
    server.RequestHandlerClass = handler(studio)
    bound = server.server_address[1]
    typer.echo(f"local URL: http://{host}:{bound}/")
    typer.echo(f"proxy URL: {proxy_url(bound)}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        studio.close()
