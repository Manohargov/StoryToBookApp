"""Exporter contract and the render-ready document model."""

from __future__ import annotations

import abc
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..domain.chapter import Chapter
from ..domain.project import Project

#: Characters that are illegal in a filename on at least one major platform.
_UNSAFE_FILENAME = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def safe_filename(text: str, fallback: str = "book") -> str:
    """Turn a title into a filename that is safe on every platform."""
    cleaned = _UNSAFE_FILENAME.sub("", (text or "").strip())
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" .")
    return (cleaned or fallback)[:120]


@dataclass
class BookDocument:
    """A snapshot of a project, ready to be rendered."""

    title: str = "Untitled Story"
    author: str = ""
    publisher: str = ""
    acknowledgment: str = ""
    author_note: str = ""
    chapters: list[Chapter] = field(default_factory=list)
    cover_path: Path | None = None
    full_text: str = ""
    language: str = "en"
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_project(cls, project: Project, cover_path: Path | None = None) -> BookDocument:
        return cls(
            title=project.display_name,
            author=project.author,
            publisher=project.publisher,
            acknowledgment=project.acknowledgment,
            author_note=project.author_note,
            chapters=list(project.chapters),
            cover_path=Path(cover_path) if cover_path else None,
            full_text=project.transcript,
        )

    @property
    def word_count(self) -> int:
        return sum(chapter.word_count for chapter in self.chapters)


class BookExporter(abc.ABC):
    """Renders a :class:`BookDocument` into a file."""

    #: Identifier used in the settings and the UI.
    name: str = "base"
    #: Human readable name.
    label: str = "Base"
    #: File extension including the dot.
    extension: str = ".bin"

    @abc.abstractmethod
    def export(self, document: BookDocument, output_dir: Path, filename_stem: str) -> Path:
        """Write the book and return the path of the created file."""

    def is_available(self) -> bool:
        """True when the exporter's dependencies are installed."""
        return True
