"""Frame geometry, tone matching, resampling and the paste-back guarantee of the extender.

A model fills the added side panels, so no model may touch the child's pixels. The photo is scaled
once to the frame height, every rendered frame is tone-matched to it over the region they share,
and the photo is pasted back at that size. A feathered border of ``feather`` pixels blends the
paste into the fill; every pixel at least ``feather`` pixels inside the photo's border is
bit-identical to the source.
"""

from dataclasses import dataclass

import numpy as np
from PIL import Image

RESAMPLE = Image.Resampling.LANCZOS  # the project's resampling filter for photos
VAE_STRIDE = 8  # every diffusion VAE in the bench encodes down by 8, so sides must be multiples
BASE_WIDTH = 1280  # width of every saved frame; the height follows from the aspect


def round_up(value: int, multiple: int) -> int:
    """Return ``value`` rounded up to the next multiple of ``multiple``."""
    return (value + multiple - 1) // multiple * multiple


@dataclass(frozen=True)
class Geometry:
    """How one photo grows into one landscape frame.

    Attributes:
        pad_left: Pixels added on the left of the photo.
        pad_right: Pixels added on the right of the photo, including the odd column and the
            stride padding when the frame width is not a multiple of the latent patch.
        pad_top: Pixels added above the photo.
        pad_bottom: Pixels added below the photo, including the stride padding.
        feather: Width in pixels of the blend band along the photo's border.
        width: Width of the saved frame.
        height: Height of the saved frame; ``pad_bottom`` carries any extra rows the VAE needs.
    """

    pad_left: int
    pad_right: int
    pad_top: int
    pad_bottom: int
    feather: int
    width: int
    height: int

    @classmethod
    def for_aspect(
        cls,
        photo_size: tuple[int, int],
        aspect: float,
        feather: int = 8,
        width: int = BASE_WIDTH,
    ) -> "Geometry":
        """Return the geometry that widens a photo to a ``width`` frame of ``aspect``.

        The width is the fixed number and the height follows from the aspect, rounded to a
        multiple of 16 so 4:3 and 16:9 at 1280 stay exact (960, 720). The photo is
        scaled to that height, so it keeps its own aspect after that one scale, and only the
        two sides are generated. The visible side pads are equal up to the odd column left by
        an odd difference. Padding to a multiple of the 16 px latent patch (8 px VAE stride
        times the 2 px transformer patch) and of the 8 px VAE stride adds at most 8 columns on
        the right; the saved frame drops them again, so the output is width x height; 3:2 at
        1024 and 1280 and 16:9 at 1920 land within 1 % of the aspect (1024x688, 1280x848,
        1920x1088).

        Args:
            photo_size: (width, height) of the photo in pixels.
            aspect: Target width / height, for example 4 / 3.
            feather: Width of the paste-back blend band.
            width: Width of the saved frame, ``BASE_WIDTH`` by default.
        """
        photo_width, photo_height = photo_size
        height = 16 * round(width / aspect / 16)
        scaled_width = round(photo_width * height / photo_height)
        side = (width - scaled_width) // 2
        stride_extra = round_up(width, 2 * VAE_STRIDE) - width
        return cls(
            pad_left=side,
            pad_right=width - scaled_width - side + stride_extra,
            pad_top=0,
            pad_bottom=round_up(height, VAE_STRIDE) - height,
            feather=feather,
            width=width,
            height=height,
        )

    def photo_size(self, photo_size: tuple[int, int]) -> tuple[int, int]:
        """Return the photo's size in the saved frame: scaled to the frame height."""
        width, height = photo_size
        return round(width * self.height / height), self.height

    def extended(self, photo_size: tuple[int, int]) -> tuple[int, int]:
        """Return the model-scale render size: the scaled photo plus every pad."""
        width, height = self.photo_size(photo_size)
        return width + self.pad_left + self.pad_right, height + self.pad_top + self.pad_bottom

    def origin(self, photo_size: tuple[int, int]) -> tuple[int, int]:
        """Return the (x, y) where the photo is pasted in the saved frame."""
        return self.pad_left, self.pad_top

    def resized(self, photo: Image.Image) -> Image.Image:
        """Return the photo at the saved frame's height, keeping its aspect."""
        return photo.resize(self.photo_size(photo.size), RESAMPLE)


def target_size(extended: tuple[int, int], factor: float = 2.0) -> tuple[int, int]:
    """Return the upscaler's output size: ``extended`` times ``factor``."""
    return round(extended[0] * factor), round(extended[1] * factor)


def render_size(target: tuple[int, int]) -> tuple[int, int]:
    """Return the size a graph renders so every side is a multiple of the VAE stride."""
    return round_up(target[0], VAE_STRIDE), round_up(target[1], VAE_STRIDE)


def crop(frame: Image.Image, size: tuple[int, int]) -> Image.Image:
    """Return the top-left ``size`` crop of a frame, dropping stride padding at the right/bottom."""
    return frame.crop((0, 0, size[0], size[1]))


def feather_mask(size: tuple[int, int], feather: int) -> Image.Image:
    """Return an ``L`` mask that is 255 in the interior and ramps to 0 at the border.

    The ramp is linear over ``feather`` pixels, so a pixel ``feather`` or more pixels inside the
    border is fully opaque and is copied unchanged.

    Args:
        size: Mask size in pixels.
        feather: Width of the ramp in pixels; 0 makes the mask fully opaque.
    """
    width, height = size
    if feather <= 0:
        return Image.new("L", size, 255)
    rows = np.minimum(np.arange(height) + 1, height - np.arange(height))
    columns = np.minimum(np.arange(width) + 1, width - np.arange(width))
    distance = np.minimum(rows[:, None], columns[None, :])
    ramp = np.clip(distance / feather, 0.0, 1.0) * 255.0
    return Image.fromarray(np.rint(ramp).astype(np.uint8), mode="L")


def tone_match(frame: Image.Image, photo: Image.Image, origin: tuple[int, int]) -> Image.Image:
    """Return ``frame`` colour-corrected so its photo region has the photo's per-channel statistics.

    Each RGB channel is shifted and scaled so that its mean and standard deviation over the
    region the photo occupies equal the photo's own. A model that re-renders the whole canvas
    shifts the colour of the scene; without this correction the pasted photo would sit in a
    visibly different exposure or white balance from the panels around it.

    Args:
        frame: The rendered frame, RGB.
        photo: The photo at the size it occupies in ``frame``.
        origin: (x, y) of the photo's top-left corner in ``frame``.
    """
    x, y = origin
    width, height = photo.size
    rendered = np.asarray(
        frame.convert("RGB").crop((x, y, x + width, y + height)), dtype=np.float64
    )
    target = np.asarray(photo.convert("RGB"), dtype=np.float64)
    result = np.asarray(frame.convert("RGB"), dtype=np.float64).copy()
    for channel in range(3):
        source = rendered[..., channel]
        reference = target[..., channel]
        source_std = source.std()
        scale = reference.std() / source_std if source_std > 1e-6 else 1.0
        result[..., channel] = (result[..., channel] - source.mean()) * scale + reference.mean()
    return Image.fromarray(np.clip(np.rint(result), 0, 255).astype(np.uint8), mode="RGB")


def seam_metrics(
    frame: Image.Image, origin: tuple[int, int], photo_size: tuple[int, int]
) -> dict[str, float]:
    """Return how smoothly the side panels continue the photo, and how much detail they hold.

    The seam ratio is the mean grey-level jump across the photo's border divided by the mean
    jump between adjacent columns inside the photo. 1.0 means the fill continues the photo's own
    texture as smoothly as the photo continues itself; a high value marks a visible seam. The
    panel standard deviation measures how much structure the new panels hold.

    Args:
        frame: The composited frame, RGB.
        origin: (x, y) of the photo's top-left corner in ``frame``.
        photo_size: (width, height) of the photo inside ``frame``.
    """
    grey = np.asarray(frame.convert("L"), dtype=np.float64)
    x, y = origin
    width, height = photo_size
    inside = grey[y : y + height, x : x + width]
    gradient = max(float(np.abs(np.diff(inside, axis=1)).mean()), 1e-6)
    left = float(np.abs(grey[y : y + height, x - 1] - grey[y : y + height, x]).mean())
    right_edge = x + width
    right = (
        float(
            np.abs(grey[y : y + height, right_edge - 1] - grey[y : y + height, right_edge]).mean()
        )
        if right_edge < grey.shape[1]
        else 0.0
    )
    panels = [grey[y : y + height, :x], grey[y : y + height, right_edge:]]
    detail = float(np.mean([panel.std() for panel in panels if panel.size]))
    return {
        "left_seam": round(left / gradient, 3),
        "right_seam": round(right / gradient, 3),
        "seam": round((left + right) / (2 * gradient), 3),
        "panel_std": round(detail, 2),
    }


def paste(
    frame: Image.Image, photo: Image.Image, origin: tuple[int, int], feather: int
) -> Image.Image:
    """Return ``frame`` with ``photo`` pasted at ``origin`` and blended over a feathered border.

    Args:
        frame: The rendered frame, RGB.
        photo: The photo at the size it occupies in ``frame``.
        origin: (x, y) of the photo's top-left corner in ``frame``.
        feather: Width of the blend band in pixels.
    """
    result = frame.convert("RGB").copy()
    result.paste(photo.convert("RGB"), origin, feather_mask(photo.size, feather))
    return result


def interior_matches(
    frame: Image.Image, photo: Image.Image, origin: tuple[int, int], feather: int
) -> bool:
    """Return True when every pixel at least ``feather`` px inside the photo is unchanged.

    Args:
        frame: The pasted frame to check, RGB.
        photo: The photo that was pasted.
        origin: (x, y) of the photo's top-left corner in ``frame``.
        feather: Width of the blend band, which is excluded from the comparison.
    """
    x, y = origin
    width, height = photo.size
    inner = (feather, feather, width - feather, height - feather)
    pasted = (x + feather, y + feather, x + width - feather, y + height - feather)
    return np.array_equal(
        np.asarray(photo.convert("RGB").crop(inner)),
        np.asarray(frame.convert("RGB").crop(pasted)),
    )
