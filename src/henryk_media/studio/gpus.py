"""The GPUs nvidia-smi reports, and the recorded peak memory each studio job needs.

The peaks are nvidia-smi ``memory.used`` of the pinned GPU during a render, minus the idle
baseline, in decimal GB; each value names the checkpoint it was read from. Portrait sizes use the
landscape row.
"""

from dataclasses import dataclass
import subprocess

QUERY = [
    "nvidia-smi",
    "--query-gpu=index,uuid,name,memory.total,memory.free,memory.used",
    "--format=csv,noheader,nounits",
]
MIB = 2**20
BYTES_PER_GB = 1e9

# data/processed/henryk-urodziny-2026/extended/4x3/checkpoints/IMG_7666.json: FLUX 3 Klein at
# 1280x960, the largest of 20 production frames; no other width is recorded, so every aspect and
# width uses it
OUTPAINT_GB = 21.317
H3_GB = {
    # data/processed/henryk-urodziny-2026/minimax-h3/checkpoints/IMG_8716.json
    ("1024x768", 5): 66.156,
    # data/processed/henryk-urodziny-2026/minimax-h3-6s/checkpoints/IMG_8564.json
    ("1024x768", 6): 67.12,
    # tmp/media/h3-speech-iter-1024/checkpoints/IMG_7667-T2.json
    ("1024x768", 10): 69.55,
    # tmp/media/h3-speech-slowmo/checkpoints/IMG_8564-M1.json (10 s); no shorter 480x320 render
    # is recorded, and a shorter clip needs no more than the 10 s one
    ("480x320", 5): 63.79,
    ("480x320", 6): 63.79,
    ("480x320", 10): 63.79,
}


@dataclass(frozen=True)
class Gpu:
    """One row of ``nvidia-smi --query-gpu``; memory in MiB."""

    index: int
    uuid: str
    name: str
    total_mib: int
    free_mib: int
    used_mib: int


def parse(text: str) -> list[Gpu]:
    """Return the GPUs of nvidia-smi's CSV output, one per non-empty line."""
    rows = [[value.strip() for value in line.split(",")] for line in text.splitlines()]
    return [
        Gpu(int(index), uuid, name, int(total), int(free), int(used))
        for index, uuid, name, total, free, used in (row for row in rows if row != [""])
    ]


def list_gpus() -> list[Gpu]:
    """Return every GPU nvidia-smi reports.

    Raises:
        subprocess.CalledProcessError: If nvidia-smi fails.
    """
    return parse(subprocess.run(QUERY, capture_output=True, text=True, check=True).stdout)


def gb(mib: int) -> float:
    """Return MiB in decimal GB."""
    return mib * MIB / BYTES_PER_GB


def need_gb(kind: str, params: dict) -> float:
    """Return the recorded peak GB of one job: ``outpaint``, or ``video`` by resolution and s."""
    if kind == "outpaint":
        return OUTPAINT_GB
    return H3_GB[(params["resolution"], params["duration"])]
