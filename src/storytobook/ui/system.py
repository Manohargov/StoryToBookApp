"""Opening files and folders with the platform's default application."""

from __future__ import annotations

import os
import platform
import subprocess
import sys
from pathlib import Path


def open_path(path: Path | str) -> bool:
    """Open a file or folder with the default handler.  Returns success."""
    target = Path(path)
    if not target.exists():
        return False

    system = platform.system()
    try:
        if system == "Windows":
            os.startfile(str(target))  # type: ignore[attr-defined]
        elif system == "Darwin":
            subprocess.Popen(["open", str(target)])
        else:
            subprocess.Popen(["xdg-open", str(target)])
    except Exception:
        return False
    return True


def reveal_in_file_manager(path: Path | str) -> bool:
    """Show a file inside the system file manager."""
    target = Path(path)
    if not target.exists():
        return False

    system = platform.system()
    try:
        if system == "Windows":
            subprocess.Popen(["explorer", "/select,", str(target)])
        elif system == "Darwin":
            subprocess.Popen(["open", "-R", str(target)])
        else:
            subprocess.Popen(["xdg-open", str(target.parent)])
    except Exception:
        return False
    return True


def default_python() -> str:
    """Path of the interpreter running the application."""
    return sys.executable
