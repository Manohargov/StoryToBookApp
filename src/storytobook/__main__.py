"""Command line entry point: ``python -m storytobook``."""

from __future__ import annotations

import sys


def main() -> int:
    """Start the graphical application."""
    try:
        import customtkinter  # noqa: F401
    except ImportError:
        sys.stderr.write(
            "StoryToBook needs 'customtkinter'.\n"
            "Install the dependencies with:  pip install -r requirements.txt\n"
        )
        return 1

    from .app import main as run_app

    return run_app()


if __name__ == "__main__":
    raise SystemExit(main())
