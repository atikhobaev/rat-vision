from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter


_MASTER_ICON = Path(__file__).resolve().parent.parent / "resources" / "brand" / "ratvision_icon.png"


@lru_cache(maxsize=1)
def _tray_subject_masks() -> tuple[Image.Image, Image.Image]:
    """Extract a simplified high-contrast rat/NVG glyph for tiny tray sizes."""
    image = Image.open(_MASTER_ICON).convert("RGBA")
    subject = Image.new("L", image.size, 0)
    green = Image.new("L", image.size, 0)
    src = image.load()
    subject_px = subject.load()
    green_px = green.load()
    for y in range(image.height):
        for x in range(image.width):
            r, g, b, a = src[x, y]
            if a < 20:
                continue
            if max(r, g, b) > 55 or (g > 45 and g > r * 1.15 and g > b * 1.15):
                subject_px[x, y] = 255
            if g > 80 and g > r * 1.15 and g > b * 1.15:
                green_px[x, y] = 255

    bbox = subject.getbbox()
    if bbox is None:
        return subject, green
    left, top, right, bottom = bbox
    pad = 0
    crop = (
        max(0, left - pad),
        max(0, top - pad),
        min(image.width, right + pad),
        min(image.height, bottom + pad),
    )
    return subject.crop(crop), green.crop(crop)


def _load_tray_brand(size: int) -> Image.Image:
    """Render a tray-specific glyph instead of shrinking the full EXE artwork."""
    subject_mask, green_mask = _tray_subject_masks()
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle(
        (0, 0, size - 1, size - 1),
        radius=max(2, round(size * 0.22)),
        fill=(2, 3, 4, 255),
    )

    available = max(1, size)
    subject = subject_mask.copy()
    subject.thumbnail((available, available), Image.Resampling.LANCZOS)
    green = green_mask.resize(subject.size, Image.Resampling.LANCZOS)

    # Crisp binary-ish masks remain legible in the 16–24 px Windows tray range.
    subject = subject.point(lambda value: 255 if value > 50 else 0)
    green = green.point(lambda value: 255 if value > 80 else 0)
    white_layer = Image.new("RGBA", subject.size, (235, 240, 241, 0))
    white_layer.putalpha(subject)
    green_layer = Image.new("RGBA", subject.size, (70, 255, 105, 0))
    green_layer.putalpha(green)
    glyph = Image.alpha_composite(white_layer, green_layer)
    image.alpha_composite(glyph, ((size - glyph.width) // 2, (size - glyph.height) // 2))
    return image


def render_tray_icon(enabled: bool, *, size: int = 32) -> Image.Image:
    """Render the approved RAT VISION NVG mark with a separate status lamp."""
    scale = size / 32.0
    image = _load_tray_brand(size)

    def p(value: float) -> int:
        return int(round(value * scale))

    lamp_center = (p(27), p(27))
    radius = max(1, p(2))
    if enabled:
        glow = Image.new("RGBA", image.size, (0, 0, 0, 0))
        gd = ImageDraw.Draw(glow)
        gd.ellipse(
            (
                lamp_center[0] - radius * 2,
                lamp_center[1] - radius * 2,
                lamp_center[0] + radius * 2,
                lamp_center[1] + radius * 2,
            ),
            fill=(57, 255, 116, 145),
        )
        glow = glow.filter(ImageFilter.GaussianBlur(max(1, p(1))))
        image = Image.alpha_composite(image, glow)
        draw = ImageDraw.Draw(image)
        draw.ellipse(
            (
                lamp_center[0] - radius,
                lamp_center[1] - radius,
                lamp_center[0] + radius,
                lamp_center[1] + radius,
            ),
            fill=(57, 255, 116, 255),
            outline=(210, 255, 222, 255),
            width=max(1, p(1)),
        )
    else:
        draw = ImageDraw.Draw(image)
        draw.ellipse(
            (
                lamp_center[0] - radius,
                lamp_center[1] - radius,
                lamp_center[0] + radius,
                lamp_center[1] + radius,
            ),
            fill=(7, 8, 9, 255),
            outline=(100, 108, 112, 255),
            width=max(1, p(1)),
        )
    return image
