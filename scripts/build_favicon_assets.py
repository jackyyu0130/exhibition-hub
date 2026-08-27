#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from PIL import Image, ImageDraw


ROOT = Path(__file__).resolve().parents[1]


def build(size: int) -> Image.Image:
    scale = size / 64
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)

    def box(values: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        return tuple(round(value * scale) for value in values)

    outer = box((5, 10, 59, 54))
    radius = max(2, round(5 * scale))
    draw.rounded_rectangle(
        outer,
        radius=radius,
        fill="#f1d89d",
        outline="#604b39",
        width=max(1, round(3 * scale)),
    )
    notch_radius = max(2, round(6 * scale))
    for center_y in (27, 37):
        draw.ellipse(
            (
                -notch_radius,
                round(center_y * scale) - notch_radius,
                notch_radius,
                round(center_y * scale) + notch_radius,
            ),
            fill=(0, 0, 0, 0),
        )
        draw.ellipse(
            (
                size - notch_radius,
                round(center_y * scale) - notch_radius,
                size + notch_radius,
                round(center_y * scale) + notch_radius,
            ),
            fill=(0, 0, 0, 0),
        )
    line_width = max(1, round(2 * scale))
    dash = max(2, round(4 * scale))
    x = round(21 * scale)
    y = round(17 * scale)
    end = round(47 * scale)
    while y < end:
        draw.line((x, y, x, min(y + dash, end)), fill="#9b7c57", width=line_width)
        y += dash * 2
    for y, width in ((21, 20), (30, 20), (39, 13)):
        draw.rounded_rectangle(
            box((29, y, 29 + width, y + 4)),
            radius=max(1, round(scale)),
            fill="#604b39",
        )
    return image


def main() -> None:
    images = {size: build(size) for size in (16, 32, 48, 64, 96, 180, 192, 512)}
    for size in (48, 96, 192, 512):
        images[size].save(ROOT / f"favicon-{size}.png", optimize=True)
    images[180].convert("RGB").save(ROOT / "apple-touch-icon.png", optimize=True)
    images[64].save(
        ROOT / "favicon.ico",
        format="ICO",
        sizes=[(16, 16), (32, 32), (48, 48), (64, 64)],
    )


if __name__ == "__main__":
    main()
