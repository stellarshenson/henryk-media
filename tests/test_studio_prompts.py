"""Tests for the H3 prompt builder and the archived production prompt preset."""

import re

from henryk_media.config import PROJ_ROOT
from henryk_media.studio.prompts import ALIGNMENT, h3_prompt, production_prompt

RECIPES = PROJ_ROOT / ".agents/skills/image-to-video/references/prompt-recipes.md"


def test_h3_prompt_matches_the_recipe_template(make_studio, serve) -> None:
    template = re.search(r"## H3 grammar\n.*?```\n(.*?)\n```", RECIPES.read_text(), re.DOTALL)
    template = template.group(1)
    assert template.splitlines()[0] == ALIGNMENT
    action = "the boy as the photo shows him; he turns his head slowly and smiles"
    camera, hold = "Static Shot", "his hands stay on the table"
    sound = "quiet room tone"
    expected = (
        template.replace(
            "<the scene as the photo shows it>; <one action with a visible start and a clear end>",
            action,
        )
        .replace("<one camera statement>", camera)
        .replace("<one hold clause>", hold)
        .replace("<non-verbal room tone and action sound>", sound)
    )
    assert h3_prompt(f" {action} ", camera, hold, sound, "") == expected
    assert h3_prompt(action, camera, hold, sound, "N/A").encode() == expected.encode()

    client = serve(make_studio())
    fields = {"action": action, "camera": camera, "hold": hold, "soundscape": sound, "music": ""}
    assert client.post("/api/h3-prompt", fields) == (200, {"prompt": expected})
    assert client.post("/api/h3-prompt", {**fields, "hold": 3})[0] == 400
    assert h3_prompt("a", "b", "c", "", "").endswith(
        "overall_soundscape: N/A\n\nnon_diegetic_music: N/A"
    )


def test_archived_production_prompt_is_offered_as_preset(make_studio, serve, image_tree) -> None:
    external = image_tree / "data/external"
    assert production_prompt("IMG_0001", external) == "he smiles and turns his head slowly"
    assert production_prompt("IMG_0003", external) == "she waves"
    assert production_prompt("WIDE_0002", external) is None

    client = serve(make_studio())
    body = client.get("/api/prompts?ref=0/IMG_0001.jpg&kind=video")[1]
    assert body == {"saved": None, "preset": {"prompt": "he smiles and turns his head slowly"}}
    body = client.get("/api/prompts?ref=2/4x3/IMG_0001.png&kind=video")[1]  # an extended frame
    assert body["preset"] == {"prompt": "he smiles and turns his head slowly"}
    assert client.get("/api/prompts?ref=0/WIDE_0002.jpg&kind=video")[1]["preset"] is None
