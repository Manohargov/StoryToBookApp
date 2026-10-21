"""Cover provider contract."""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

ProgressCallback = Any  # Callable[[str], None]


@dataclass
class CoverRequest:
    """Everything a cover provider needs to draw a book cover."""

    story_text: str = ""
    title: str = ""
    author: str = ""
    output_path: Path = field(default_factory=lambda: Path("cover.png"))
    width: int = 1200
    height: int = 1600
    steps: int = 30
    guidance_scale: float = 7.5
    seed: int = -1
    extra_prompt: str = ""


@dataclass
class CoverResult:
    """The outcome of a cover generation run."""

    path: Path
    provider: str = ""
    prompt: str = ""
    genre: str = ""


class CoverProvider(abc.ABC):
    """Produces the cover image for a book."""

    #: Stable identifier used in the settings file.
    name: str = "base"
    #: Human readable name shown in the interface.
    label: str = "Base"
    #: What the provider needs in order to work.
    requirements: str = ""

    def __init__(self, settings=None) -> None:
        self.settings = settings

    @abc.abstractmethod
    def is_available(self) -> bool:
        """True when the provider can run right now."""

    @abc.abstractmethod
    def generate(self, request: CoverRequest, progress: ProgressCallback | None = None) -> CoverResult:
        """Render a cover and save it to ``request.output_path``."""

    def status(self) -> str:
        """Short human readable availability message."""
        if self.is_available():
            return "Ready"
        return self.requirements or "Not available"
