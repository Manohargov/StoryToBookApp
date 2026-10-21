"""Font discovery and text drawing helpers shared by the cover providers."""

from __future__ import annotations

import sys
from functools import lru_cache
from pathlib import Path

from PIL import ImageDraw, ImageFont

#: Font files tried for headings and body text, in order of preference.
_BOLD_CANDIDATES = {
    "Windows": [
        r"C:\Windows\Fonts\georgiab.ttf",
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf",
        r"C:\Windows\Fonts\calibrib.ttf",
    ],
    "Darwin": [
        "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial Bold.ttf",
    ],
    "Linux": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ],
}

_REGULAR_CANDIDATES = {
    "Windows": [
        r"C:\Windows\Fonts\georgia.ttf",
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\calibri.ttf",
    ],
    "Darwin": [
        "/System/Library/Fonts/Supplemental/Georgia.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial.ttf",
    ],
    "Linux": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ],
}


_ITALIC_CANDIDATES = {
    "Windows": [
        r"C:\Windows\Fonts\georgiai.ttf",
        r"C:\Windows\Fonts\ariali.ttf",
        r"C:\Windows\Fonts\segoeuii.ttf",
        r"C:\Windows\Fonts\calibrii.ttf",
    ],
    "Darwin": [
        "/System/Library/Fonts/Supplemental/Georgia Italic.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/Library/Fonts/Arial Italic.ttf",
    ],
    "Linux": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Italic.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Oblique.ttf",
    ],
}


def _platform_key() -> str:
    if sys.platform.startswith("win"):
        return "Windows"
    if sys.platform == "darwin":
        return "Darwin"
    return "Linux"


@lru_cache(maxsize=32)
def find_font(bold: bool = False, italic: bool = False) -> str | None:
    """Path of a usable TrueType font, or ``None`` when none was found.

    ``italic`` takes precedence over ``bold`` when both are requested, since
    no combined bold-italic file is listed.
    """
    if italic:
        candidates = _ITALIC_CANDIDATES
    elif bold:
        candidates = _BOLD_CANDIDATES
    else:
        candidates = _REGULAR_CANDIDATES
    for path in candidates.get(_platform_key(), []):
        if Path(path).exists():
            return path
    return None


@lru_cache(maxsize=64)
def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a font at ``size``, falling back to Pillow's bundled default."""
    path = find_font(bold=bold)
    if path:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            pass
    try:
        return ImageFont.load_default(size=size)
    except TypeError:  # pragma: no cover - very old Pillow
        return ImageFont.load_default()


def text_size(draw: ImageDraw.ImageDraw, text: str, font) -> tuple[int, int]:
    """Width and height of ``text`` rendered with ``font``."""
    if not text:
        return 0, 0
    try:
        left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
        return int(right - left), int(bottom - top)
    except (AttributeError, OSError):  # pragma: no cover - legacy Pillow
        return draw.textsize(text, font=font)


def wrap_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> list[str]:
    """Wrap ``text`` so that no line is wider than ``max_width`` pixels."""
    words = (text or "").split()
    if not words:
        return []

    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        width, _ = text_size(draw, candidate, font)
        if width <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def fit_font(
    draw: ImageDraw.ImageDraw,
    text: str,
    max_width: int,
    max_height: int,
    max_size: int,
    min_size: int = 18,
    bold: bool = True,
    line_spacing: float = 1.15,
):
    """Pick the largest font size at which ``text`` fits the given box.

    Returns the font and the wrapped lines.
    """
    size = max_size
    while size > min_size:
        font = load_font(size, bold=bold)
        lines = wrap_text(draw, text, font, max_width)
        _, line_height = text_size(draw, "Ag", font)
        total_height = int(line_height * line_spacing * len(lines))
        if total_height <= max_height and len(lines) <= 4:
            return font, lines
        size -= 2
    font = load_font(min_size, bold=bold)
    return font, wrap_text(draw, text, font, max_width)


def draw_centered_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font,
    center_x: int,
    y: int,
    fill: tuple[int, int, int],
    stroke_width: int = 0,
    stroke_fill: tuple[int, int, int] = (0, 0, 0),
    line_spacing: float = 1.15,
) -> int:
    """Draw centred text, returning the y position just below it."""
    lines = text.split("\n") if "\n" in text else [text]
    _, line_height = text_size(draw, "Ag", font)
    step = int(line_height * line_spacing)
    for line in lines:
        width, _ = text_size(draw, line, font)
        draw.text(
            (center_x - width // 2, y),
            line,
            font=font,
            fill=fill,
            stroke_width=stroke_width,
            stroke_fill=stroke_fill,
        )
        y += step
    return y
