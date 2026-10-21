"""Transcription provider contract."""

from __future__ import annotations

import abc
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

ProgressCallback = Callable[[str], None]


@dataclass
class TranscriptionSegment:
    """A timed piece of the recording."""

    start: float = 0.0
    end: float = 0.0
    text: str = ""

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)


@dataclass
class TranscriptionResult:
    """The outcome of a transcription run."""

    text: str = ""
    segments: list[TranscriptionSegment] = field(default_factory=list)
    provider: str = ""
    language: str = ""

    @property
    def duration(self) -> float:
        return max((s.end for s in self.segments), default=0.0)


class TranscriptionProvider(abc.ABC):
    """Turns an audio file into text."""

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
    def transcribe(
        self, audio_path: Path, progress: ProgressCallback | None = None
    ) -> TranscriptionResult:
        """Transcribe ``audio_path``."""

    def status(self) -> str:
        """Short human readable availability message."""
        if self.is_available():
            return "Ready"
        return self.requirements or "Not available"
