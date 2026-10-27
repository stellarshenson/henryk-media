"""The image extender's server, graphs and models, read from one JSON file."""

from dataclasses import dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class Setup:
    """One ComfyUI server, its work folders, the graphs and the model descriptions.

    Attributes:
        gpu: nvidia-smi UUID of the GPU the server runs on.
        port: Port of the server on 127.0.0.1.
        launch_command: Shell command that starts the server detached.
        stop_command: Shell command that stops it.
        io_dirs: The server's input, output and temp folders.
        graphs: Graph template file per graph name.
        paths: Absolute paths the graphs need, such as a local diffusers folder.
    """

    gpu: str
    port: int
    launch_command: str
    stop_command: str
    io_dirs: dict[str, Path]
    graphs: dict[str, Path]
    paths: dict[str, str]

    @classmethod
    def load(cls, path: Path) -> "Setup":
        """Return the setup recorded in a JSON file; ``gpu`` keeps only its UUID."""
        data = json.loads(path.read_text())
        return cls(
            gpu=data["gpu"].split()[0],
            port=data["port"],
            launch_command=data["launch_command"],
            stop_command=data["stop_command"],
            io_dirs={name: Path(value) for name, value in data["io_dirs"].items()},
            graphs={name: Path(value) for name, value in data["graphs"].items()},
            paths=dict(data.get("paths", {})),
        )
