"""The GPUs nvidia-smi reports, and the peak memory each studio job is estimated to need.

The peaks are nvidia-smi ``memory.used`` of the pinned GPU during a render, minus the idle
baseline, in decimal GB; each value names the checkpoint it was read from. The H3 rows were
recorded at 1024x768 and 480x320; a clip of another rendered size is estimated between them. The
Klein rows were recorded at four frame sizes; a frame is estimated from its pixel count.
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

KLEIN_GB = {  # FLUX 3 Klein frame jobs, keyed by the frame's pixel count
    # data/processed/henryk-urodziny-2026/extended/4x3/checkpoints/IMG_7666.json, the largest of
    # 20 production frames
    1280 * 960: 21.317,
    # tmp/workflows/studio/reshoot-live.json frame_checks.square, outpaint and uhd_frame (GPU 1)
    1080 * 1080: 21.43,
    1920 * 1080: 22.08,
    3840 * 2160: 27.48,
}
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
H3_PIXELS = {"480x320": 480 * 320, "1024x768": 1024 * 768}  # rendered pixels of the H3 rows


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


def choose(
    rows: list[Gpu], need: float, server_gpu: str | None = None, server_mib: int = 0
) -> Gpu | None:
    """Return the most capable GPU that holds ``need`` now, or None.

    A GPU qualifies when the need fits its total and its free memory plus, on the server's GPU,
    the memory the studio's own ComfyUI server holds (``server_mib``); the most capable is the
    largest total.
    """
    room = [
        row
        for row in rows
        if need <= gb(row.total_mib)
        and need <= gb(row.free_mib + (server_mib if row.uuid == server_gpu else 0))
    ]
    return max(room, key=lambda row: row.total_mib, default=None)


def need_gb(kind: str, params: dict) -> float:
    """Return the peak GB of one job: ``outpaint`` estimated from the frame's pixels
    (``params["size"]``), ``video`` from the rendered pixels (``params["render"]``) and the
    seconds."""
    if kind == "outpaint":
        # shortcut: linear in the frame's pixels between the measured 1280x960 and 3840x2160 rows,
        # never below the 1280x960 row, extrapolated beyond UHD 4K; measure a larger frame first
        low, high = 1280 * 960, 3840 * 2160
        share = max(0, params["size"][0] * params["size"][1] - low) / (high - low)
        return round(KLEIN_GB[low] + (KLEIN_GB[high] - KLEIN_GB[low]) * share, 3)
    # shortcut: linear in the rendered pixels through the 480x320 and 1024x768 rows of the same
    # duration, extrapolated beyond 1024x768; replace with a measured row for each larger preset
    low, high = (H3_GB[(size, params["duration"])] for size in H3_PIXELS)
    pixels = params["render"][0] * params["render"][1]
    share = (pixels - H3_PIXELS["480x320"]) / (H3_PIXELS["1024x768"] - H3_PIXELS["480x320"])
    return round(low + (high - low) * share, 3)
