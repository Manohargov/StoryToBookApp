"""Headless smoke test: build every page and exercise the navigation."""

from __future__ import annotations

import os
import sys
import tempfile

os.environ.setdefault("STORYTOBOOK_HOME", tempfile.mkdtemp(prefix="stb-smoke-"))
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))

from storytobook.app import StoryApp  # noqa: E402
from storytobook.ui.theme import apply_theme  # noqa: E402


def main() -> int:
    apply_theme("dark", "blue")
    app = StoryApp()
    app.update_idletasks()
    app.update()

    for name in (
        "LandingPage",
        "DashboardPage",
        "RecordingPage",
        "TranscriptPage",
        "DetailsPage",
        "ExportPage",
        "SettingsPage",
    ):
        app.navigate(name)
        app.update_idletasks()
        app.update()
        print(f"  navigated to {name}")

    app.destroy()
    print("SMOKE TEST OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
