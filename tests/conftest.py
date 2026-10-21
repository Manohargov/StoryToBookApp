"""Shared pytest fixtures.

Every test runs against a throwaway data directory so the developer's real
library is never touched.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


@pytest.fixture(autouse=True)
def isolated_home(tmp_path, monkeypatch):
    """Point the application at a temporary data directory."""
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("STORYTOBOOK_HOME", str(home))
    yield home


@pytest.fixture
def settings():
    from storytobook.settings import AppSettings

    return AppSettings()


@pytest.fixture
def library(tmp_path):
    from storytobook.services.library import Library

    return Library(tmp_path / "library")


@pytest.fixture
def project(library):
    """An empty project inside a temporary library."""
    return library.create(title="The Quiet Harbour")


SAMPLE_TEXT = (
    "Chapter 1 The Crossing. The ferry left the harbour at dawn and the sea was "
    "flat as a sheet of tin. Maren stood at the rail and watched the town "
    "shrink into the mist behind her. She had told herself she would not look "
    "back, and yet she looked. "
    "Chapter 2 The Island. The island appeared an hour before noon, a low green "
    "shape that seemed to rise out of the water rather than rest on it. Nobody "
    "came to meet them. The harbour was a single wooden pier, bleached nearly "
    "white by the sun, and a woman in a red coat who watched them land. "
    "Chapter 3 The House. The house was built of stone that had gone grey with "
    "weather, and it had more windows than Maren could count. Inside, the air "
    "smelled of dust and old smoke. A lamp burned on a table though no one had "
    "lit it. "
    "Chapter 4 The Names. They found the books in the cellar, row upon row of "
    "them, their spines faded to a soft grey. Every book was the same book. "
    "Maren opened one at random and found her own handwriting on the first "
    "page, and her own name at the top of it. "
    "Chapter 5 The Turning. The storm came in the night. It came from the sea "
    "and it did not stop, and in the morning the harbour was gone. Maren stood "
    "at the window of the house and watched the water climb the steps. "
)
