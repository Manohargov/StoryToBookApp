"""Filesystem locations used by the application.

Everything the app writes lives under a single platform-appropriate data
directory so a project can be backed up or moved as one unit.  The location
can be overridden with the ``STORYTOBOOK_HOME`` environment variable, which
is what the test-suite uses to stay hermetic.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

APP_NAME = "StoryToBook"

#: Root of the installed package (``src/storytobook``).
PACKAGE_ROOT = Path(__file__).resolve().parent

#: Repository root when running from a source checkout.
PROJECT_ROOT = PACKAGE_ROOT.parent.parent


def _data_root() -> Path:
    override = os.environ.get("STORYTOBOOK_HOME")
    if override:
        return Path(override).expanduser().resolve()

    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA") or (Path.home() / "AppData" / "Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library" / "Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME") or (Path.home() / ".local" / "share"))
    return base / APP_NAME


def data_dir() -> Path:
    """Root directory for application data."""
    return _data_root()


def settings_file() -> Path:
    """Location of the persisted user settings file."""
    return data_dir() / "settings.json"


def library_dir() -> Path:
    """Directory holding one sub-directory per project."""
    return data_dir() / "library"


def logs_dir() -> Path:
    """Directory for application logs."""
    return data_dir() / "logs"


def assets_dir() -> Path:
    """Bundled assets shipped with the source checkout (fonts, LoRA adapters)."""
    return PROJECT_ROOT / "assets"


def ensure_data_dirs() -> Path:
    """Create the data directory tree and return its root."""
    root = data_dir()
    for path in (root, library_dir(), logs_dir()):
        path.mkdir(parents=True, exist_ok=True)
    return root
