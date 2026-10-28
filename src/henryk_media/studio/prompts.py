"""Preset prompts, the MiniMax H3 prompt grammar and the prompts saved per image and job kind.

The outpaint texts are verbatim from ``.agents/skills/image-outpainting/references/
extender-recipe.md``; the alignment line is the exact first line of the H3 grammar in
``.agents/skills/image-to-video/references/prompt-recipes.md``.
"""

import hashlib
import json
import os
from pathlib import Path
import re

from henryk_media.config import EXTERNAL_DATA_DIR

ALIGNMENT = (
    "For the target video, at 0.00 seconds into the target video, <Picture 1> (from [Shot 1]) "
    "is fully referenced."
)
OUTPAINT_PROMPT = (
    "Outpaint the image: replace the solid grey areas with an empty continuation of the same "
    "room and scene beyond the frame, keeping the existing picture unchanged. Continue the same "
    "floor, the same wall and background and the same soft indoor daylight as the photo, at the "
    "same perspective, scale and brightness. The added area holds no person, no child, no face, "
    "no hands and no figure; keep every person already in the photo exactly as they are, with "
    "the same faces, expressions, hair and clothes."
)
OUTPAINT_NEGATIVE = (
    "person, child, man, woman, crowd, face, hands, portrait, new person, extra person, second "
    "child, mirrored child, reflected child, reflection of a person, different face, changed "
    "expression, deformed, distorted, blurry, low quality, text, watermark"
)
OUTPAINT_PRESET = {"prompt": OUTPAINT_PROMPT, "negative_prompt": OUTPAINT_NEGATIVE, "cfg": 1.0}


def h3_prompt(action: str, camera: str, hold: str, soundscape: str, music: str) -> str:
    """Return the five prompter fields in the H3 grammar; an empty audio field becomes N/A."""
    action, camera, hold, soundscape, music = (
        value.strip() for value in (action, camera, hold, soundscape, music)
    )
    return (
        f"{ALIGNMENT}\n\n"
        f"integrated_multimodal_description: [Shot 1] {action}; {camera}; {hold}\n\n"
        f"overall_soundscape: {soundscape or 'N/A'}\n\n"
        f"non_diegetic_music: {music or 'N/A'}"
    )


def production_prompt(stem: str, external: Path = EXTERNAL_DATA_DIR) -> str | None:
    """Return the first fenced block under ``## <stem>`` in a campaign's archived H3 prompts."""
    for path in sorted(external.glob("*/prompts/image-to-video-h3.md")):
        for section in re.split(r"^## ", path.read_text(), flags=re.MULTILINE)[1:]:
            heading, _, body = section.partition("\n")
            block = re.search(r"^```[^\n]*\n(.*?)\n```", body, re.MULTILINE | re.DOTALL)
            if heading.strip() == stem and block:
                return block.group(1)
    return None


def prompt_file(folder: Path, kind: str, source: Path) -> Path:
    """Return the saved-prompt file of one job kind on one resolved source."""
    digest = hashlib.sha1(str(source).encode()).hexdigest()[:16]
    return folder / f"{kind}-{digest}.json"


def load_saved(folder: Path, kind: str, source: Path) -> dict | None:
    """Return the fields last submitted for this kind and source, or None."""
    path = prompt_file(folder, kind, source)
    return json.loads(path.read_text())["fields"] if path.exists() else None


def save_submitted(folder: Path, kind: str, source: Path, fields: dict) -> None:
    """Save the submitted fields for this kind and source, replacing the file atomically."""
    path = prompt_file(folder, kind, source)
    staged = path.with_name(path.name + ".tmp")
    staged.write_text(json.dumps({"source": str(source), "fields": fields}, indent=2))
    os.replace(staged, path)
