"""Capture a screenshot of the running application.

Usage:  python scripts/screenshot.py <page> <output.png>
"""

from __future__ import annotations

import os
import sys
import tempfile

os.environ.setdefault("STORYTOBOOK_HOME", tempfile.mkdtemp(prefix="stb-shot-"))
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))

from PIL import ImageGrab  # noqa: E402

from storytobook.app import StoryApp  # noqa: E402
from storytobook.ui.theme import apply_theme  # noqa: E402


def main() -> int:
    page = sys.argv[1] if len(sys.argv) > 1 else "LandingPage"
    output = sys.argv[2] if len(sys.argv) > 2 else "screenshot.png"

    apply_theme("dark", "blue")
    app = StoryApp()
    app.geometry("1180x760+40+40")
    app.update_idletasks()
    app.update()

    app.navigate(page)
    app.update_idletasks()
    app.update()

    def capture() -> None:
        app.update_idletasks()
        app.update()
        ImageGrab.grab().save(output)
        app.destroy()

    app.after(1200, capture)
    app.mainloop()
    print(f"saved {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
