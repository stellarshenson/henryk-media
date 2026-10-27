"""Build one labelled contact sheet from a matrix of tiles.

The sheet is written to disk; the notebook displays it by link. Every tile has the same size, the
image fitted inside it and the label in a bar below, so a reader compares pictures rather than
layout. A text-only tile marks a row or column header.
"""

from dataclasses import dataclass
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

TILE_WIDTH = 560  # pixels of every tile's image box, wide enough for a full model-pair label
TILE_HEIGHT = 420  # pixels of every tile's image box
LABEL_HEIGHT = 28  # pixels of the label bar under every tile
BACKGROUND = (32, 32, 32)  # sheet background
BOX = (48, 48, 48)  # letterbox behind an image that does not fill its tile
TEXT = (240, 240, 240)  # label colour
FONT_PATHS = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",
)


@dataclass(frozen=True)
class Tile:
    """One cell of a contact sheet.

    Attributes:
        image: Image file shown in the tile, None for a text-only header tile.
        label: Text under the tile.
    """

    image: Path | None
    label: str


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Return a TrueType font at ``size``, or Pillow's built-in font when none is installed."""
    for path in FONT_PATHS:
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size=size)


def _draw_tile(sheet: Image.Image, tile: Tile, x: int, y: int, label_size: int = 14) -> None:
    """Draw one tile with its letterboxed image and label bar at (x, y)."""
    draw = ImageDraw.Draw(sheet)
    draw.rectangle((x, y, x + TILE_WIDTH - 1, y + TILE_HEIGHT - 1), fill=BOX)
    if tile.image is not None:
        with Image.open(tile.image) as opened:
            image = opened.convert("RGB")
        image.thumbnail((TILE_WIDTH, TILE_HEIGHT), Image.Resampling.LANCZOS)
        sheet.paste(
            image, (x + (TILE_WIDTH - image.width) // 2, y + (TILE_HEIGHT - image.height) // 2)
        )
    label_font = font(label_size if tile.image is not None else 19)
    text = tile.label
    while draw.textlength(text, font=label_font) > TILE_WIDTH - 8 and len(text) > 4:
        text = text[:-2]
    draw.text((x + 4, y + TILE_HEIGHT + 6), text, fill=TEXT, font=label_font)


def contact_sheet(grid: list[list[Tile]], path: Path, label_size: int = 14) -> Path:
    """Write a contact sheet and its Markdown index for a rectangular matrix of tiles.

    Args:
        grid: Rows of tiles; every row must have the same length.
        path: Destination PNG; the Markdown index is written beside it.
        label_size: Font size of an image tile's label, in pixels.

    Returns:
        The PNG path.

    Raises:
        ValueError: If the grid is empty or ragged.
    """
    if not grid or not grid[0]:
        raise ValueError("the grid is empty")
    columns = len(grid[0])
    if any(len(row) != columns for row in grid):
        raise ValueError("the grid is ragged; every row must have the same number of tiles")
    sheet = Image.new(
        "RGB",
        (columns * TILE_WIDTH, len(grid) * (TILE_HEIGHT + LABEL_HEIGHT)),
        BACKGROUND,
    )
    for row_index, row in enumerate(grid):
        for column_index, tile in enumerate(row):
            _draw_tile(
                sheet,
                tile,
                column_index * TILE_WIDTH,
                row_index * (TILE_HEIGHT + LABEL_HEIGHT),
                label_size,
            )
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path)
    lines = [
        f"# {path.name}",
        "",
        "Every tile is labelled; the top-left corner is the source photo.",
        "",
        "| Row | Column | Tile |",
        "|---:|---:|---|",
    ]
    for row_index, row in enumerate(grid):
        for column_index, tile in enumerate(row):
            lines.append(f"| {row_index + 1} | {column_index + 1} | {tile.label} |")
    path.with_suffix(".md").write_text("\n".join(lines) + "\n")
    return path
