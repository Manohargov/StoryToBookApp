"""The persisted project model."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from .chapter import Chapter
from .text import word_count


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


class ProjectStatus(str, Enum):
    """Where a project is in its life cycle."""

    DRAFT = "draft"
    RECORDED = "recorded"
    TRANSCRIBED = "transcribed"
    ILLUSTRATED = "illustrated"
    EXPORTED = "exported"

    @property
    def label(self) -> str:
        return {
            ProjectStatus.DRAFT: "Draft",
            ProjectStatus.RECORDED: "Audio recorded",
            ProjectStatus.TRANSCRIBED: "Transcript ready",
            ProjectStatus.ILLUSTRATED: "Cover ready",
            ProjectStatus.EXPORTED: "Published",
        }[self]


@dataclass
class Project:
    """A book being written."""

    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    title: str = "Untitled Story"
    author: str = ""
    publisher: str = ""
    acknowledgment: str = ""
    author_note: str = ""
    transcript: str = ""
    chapters: list[Chapter] = field(default_factory=list)
    status: ProjectStatus = ProjectStatus.DRAFT
    cover_filename: str = ""
    audio_filename: str = ""
    exports: list[dict[str, Any]] = field(default_factory=list)
    notes: str = ""
    created_at: str = field(default_factory=_now)
    updated_at: str = field(default_factory=_now)

    # ------------------------------------------------------------------ #
    @property
    def word_count(self) -> int:
        return word_count(self.transcript)

    @property
    def chapter_count(self) -> int:
        return len(self.chapters)

    @property
    def display_name(self) -> str:
        return (self.title or "").strip() or "Untitled Story"

    def touch(self) -> None:
        """Mark the project as modified just now."""
        self.updated_at = _now()

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "author": self.author,
            "publisher": self.publisher,
            "acknowledgment": self.acknowledgment,
            "author_note": self.author_note,
            "transcript": self.transcript,
            "chapters": [c.to_dict() for c in self.chapters],
            "status": self.status.value,
            "cover_filename": self.cover_filename,
            "audio_filename": self.audio_filename,
            "exports": list(self.exports),
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Project:
        chapters_raw = data.get("chapters") or []
        chapters = [
            c if isinstance(c, Chapter) else Chapter.from_dict(c)
            for c in chapters_raw
        ]
        try:
            status = ProjectStatus(data.get("status", ProjectStatus.DRAFT.value))
        except ValueError:
            status = ProjectStatus.DRAFT

        return cls(
            id=data.get("id") or uuid.uuid4().hex[:12],
            title=data.get("title", "Untitled Story"),
            author=data.get("author", ""),
            publisher=data.get("publisher", ""),
            acknowledgment=data.get("acknowledgment", ""),
            author_note=data.get("author_note", ""),
            transcript=data.get("transcript", ""),
            chapters=chapters,
            status=status,
            cover_filename=data.get("cover_filename", ""),
            audio_filename=data.get("audio_filename", ""),
            exports=list(data.get("exports") or []),
            notes=data.get("notes", ""),
            created_at=data.get("created_at") or _now(),
            updated_at=data.get("updated_at") or _now(),
        )
