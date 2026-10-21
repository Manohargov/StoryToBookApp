"""Generate the application icon.

Creates a 1024 x 1024 PNG master image, and from it:

* ``StoryToBook.ico``   - the Windows icon (multi-resolution)
* ``StoryToBook.icns``  - the macOS icon (built with ``iconutil``)

Usage::

    python packaging/make_icon.py packaging/assets
"""

from __future__ import annotations

import math
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw

BACKGROUND_TOP = (28, 32, 56)
BACKGROUND_BOTTOM = (12, 14, 24)
ACCENT = (94, 150, 255)
GOLD = (232, 196, 128)
PAPER = (244, 240, 230)


def _rounded_mask(size: int) -> Image.Image:
    mask = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(mask)
    draw.rounded_rectangle([0, 0, size - 1, size - 1], radius=int(size * 0.22), fill=255)
    return mask


def build_master(size: int = 1024) -> Image.Image:
    """Draw the icon: an open book with a glowing page."""
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    # Background plate.
    plate = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    plate_draw = ImageDraw.Draw(plate)
    for y in range(size):
        ratio = y / max(1, size - 1)
        eased = ratio * ratio * (3 - 2 * ratio)
        colour = tuple(
            int(BACKGROUND_TOP[i] + (BACKGROUND_BOTTOM[i] - BACKGROUND_TOP[i]) * eased)
            for i in range(3)
        )
        plate_draw.line([(0, y), (size, y)], fill=(*colour, 255))
    plate.putalpha(_rounded_mask(size))
    image.alpha_composite(plate)

    draw = ImageDraw.Draw(image)
    centre = size / 2

    # Soft glow behind the book.
    glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse(
        [centre - size * 0.34, centre - size * 0.30, centre + size * 0.34, centre + size * 0.38],
        fill=(*ACCENT, 90),
    )
    from PIL import ImageFilter

    glow = glow.filter(ImageFilter.GaussianBlur(radius=size * 0.09))
    image.alpha_composite(glow)
    draw = ImageDraw.Draw(image)

    # The open book: two pages meeting at a spine.
    left = [
        (centre - size * 0.30, centre - size * 0.20),
        (centre - size * 0.02, centre - size * 0.12),
        (centre - size * 0.02, centre + size * 0.24),
        (centre - size * 0.30, centre + size * 0.17),
    ]
    right = [
        (centre + size * 0.02, centre - size * 0.12),
        (centre + size * 0.30, centre - size * 0.20),
        (centre + size * 0.30, centre + size * 0.17),
        (centre + size * 0.02, centre + size * 0.24),
    ]
    draw.polygon(left, fill=(*PAPER, 255))
    draw.polygon(right, fill=(*PAPER, 240))

    # Spine.
    draw.polygon(
        [
            (centre - size * 0.03, centre - size * 0.125),
            (centre + size * 0.03, centre - size * 0.125),
            (centre + size * 0.03, centre + size * 0.245),
            (centre - size * 0.03, centre + size * 0.245),
        ],
        fill=(*GOLD, 255),
    )

    # Lines of text on the left page.
    for index in range(5):
        y = centre - size * 0.05 + index * size * 0.055
        draw.line(
            [
                (centre - size * 0.26, y),
                (centre - size * 0.06 - index * size * 0.008, y),
            ],
            fill=(*(70, 76, 100), 190),
            width=max(2, int(size * 0.011)),
        )

    # A spark above the book.
    spark_x, spark_y = centre + size * 0.16, centre - size * 0.30
    for angle in range(0, 360, 45):
        radians = math.radians(angle)
        length = size * 0.075 if angle % 90 == 0 else size * 0.045
        draw.line(
            [
                (spark_x, spark_y),
                (spark_x + math.cos(radians) * length, spark_y + math.sin(radians) * length),
            ],
            fill=(*GOLD, 255),
            width=max(3, int(size * 0.016)),
        )

    return image


def write_ico(master: Image.Image, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    master.save(target, format="ICO", sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])


def write_icns(master: Image.Image, target: Path) -> bool:
    """Build an ``.icns`` file.  Only possible on macOS, where iconutil lives."""
    import shutil
    import tempfile

    if not shutil.which("iconutil"):
        return False

    with tempfile.TemporaryDirectory() as tmp:
        iconset = Path(tmp) / "StoryToBook.iconset"
        iconset.mkdir()
        for base in (16, 32, 128, 256, 512):
            scaled = master.resize((base, base), Image.LANCZOS)
            scaled.save(iconset / f"icon_{base}x{base}.png")
            scaled.save(iconset / f"icon_{base // 2}x{base // 2}@2x.png")
        subprocess.run(
            ["iconutil", "-c", "icns", str(iconset), "-o", str(target)],
            check=True,
        )
    return True


def main() -> int:
    out_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "packaging/assets")
    out_dir.mkdir(parents=True, exist_ok=True)

    master = build_master()
    master.save(out_dir / "icon.png")

    write_ico(master, out_dir / "StoryToBook.ico")
    print(f"wrote {out_dir / 'StoryToBook.ico'}")

    if write_icns(master, out_dir / "StoryToBook.icns"):
        print(f"wrote {out_dir / 'StoryToBook.icns'}")
    else:
        print("iconutil not available - skipping the .icns file")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
