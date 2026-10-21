"""Project library: a folder per project on disk.

Layout::

    <library root>/
        <project id>/
            project.json      metadata, transcript and chapters
            transcript.txt     plain text copy of the transcript
            audio/source.wav   the recording
            cover.png          generated cover art
            exports/           rendered books
"""

from __future__ import annotations

import json
import os
import shutil
from pathlib import Path

from .. import paths
from ..domain.project import Project
from ..errors import ProjectNotFoundError

_PROJECT_FILE = "project.json"


class Library:
    """Create, load, list and delete projects."""

    def __init__(self, root: Path | None = None) -> None:
        self.root = Path(root) if root is not None else paths.library_dir()
        self.root.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------ #
    # Locations
    # ------------------------------------------------------------------ #
    def project_dir(self, project_id: str) -> Path:
        return self.root / project_id

    def audio_dir(self, project_id: str) -> Path:
        return self.project_dir(project_id) / "audio"

    def exports_dir(self, project_id: str) -> Path:
        return self.project_dir(project_id) / "exports"

    def audio_path(self, project_id: str) -> Path:
        return self.audio_dir(project_id) / "source.wav"

    def transcript_path(self, project_id: str) -> Path:
        return self.project_dir(project_id) / "transcript.txt"

    def cover_path(self, project_id: str) -> Path:
        return self.project_dir(project_id) / "cover.png"

    def export_path(self, project_id: str, filename: str) -> Path:
        return self.exports_dir(project_id) / filename

    # ------------------------------------------------------------------ #
    # CRUD
    # ------------------------------------------------------------------ #
    def create(self, title: str = "Untitled Story") -> Project:
        """Create a new project directory and return the project."""
        project = Project(title=title or "Untitled Story")
        directory = self.project_dir(project.id)
        for path in (directory, self.audio_dir(project.id), self.exports_dir(project.id)):
            path.mkdir(parents=True, exist_ok=True)
        self.save(project)
        return project

    def list(self) -> list[Project]:
        """All projects, most recently updated first."""
        projects: list[Project] = []
        for entry in self.root.iterdir():
            if not entry.is_dir():
                continue
            if not (entry / _PROJECT_FILE).exists():
                continue
            try:
                projects.append(self.load(entry.name))
            except (ProjectNotFoundError, json.JSONDecodeError, OSError):
                continue
        projects.sort(key=lambda p: p.updated_at, reverse=True)
        return projects

    def load(self, project_id: str) -> Project:
        """Read a project from disk."""
        file_path = self.project_dir(project_id) / _PROJECT_FILE
        if not file_path.exists():
            raise ProjectNotFoundError(f"No project with id {project_id!r}")
        data = json.loads(file_path.read_text(encoding="utf-8"))
        return Project.from_dict(data)

    def save(self, project: Project) -> Path:
        """Write a project to disk atomically."""
        directory = self.project_dir(project.id)
        directory.mkdir(parents=True, exist_ok=True)
        self.audio_dir(project.id).mkdir(parents=True, exist_ok=True)
        self.exports_dir(project.id).mkdir(parents=True, exist_ok=True)

        project.touch()
        target = directory / _PROJECT_FILE
        tmp = target.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(project.to_dict(), indent=2, ensure_ascii=False), encoding="utf-8")
        os.replace(tmp, target)

        if project.transcript:
            self.transcript_path(project.id).write_text(project.transcript, encoding="utf-8")
        return target

    def delete(self, project_id: str) -> None:
        """Remove a project and everything it produced."""
        directory = self.project_dir(project_id)
        if not directory.exists():
            raise ProjectNotFoundError(f"No project with id {project_id!r}")
        shutil.rmtree(directory, ignore_errors=True)

    def duplicate(self, project_id: str) -> Project:
        """Copy a project, including its audio and cover."""
        source = self.load(project_id)
        copy = self.create(title=f"{source.display_name} (copy)")
        copy.author = source.author
        copy.publisher = source.publisher
        copy.acknowledgment = source.acknowledgment
        copy.author_note = source.author_note
        copy.transcript = source.transcript
        copy.chapters = list(source.chapters)
        copy.notes = source.notes

        audio = self.audio_path(project_id)
        if audio.exists():
            shutil.copy2(audio, self.audio_path(copy.id))
            copy.audio_filename = "source.wav"

        cover = self.cover_path(project_id)
        if cover.exists():
            shutil.copy2(cover, self.cover_path(copy.id))
            copy.cover_filename = "cover.png"

        self.save(copy)
        return copy

    # ------------------------------------------------------------------ #
    def record_export(self, project: Project, path: Path, fmt: str) -> None:
        """Remember that a file was exported for this project."""
        entry = {
            "path": str(path),
            "format": fmt,
            "created_at": project.updated_at,
            "size": path.stat().st_size if path.exists() else 0,
        }
        project.exports = [e for e in project.exports if e.get("path") != entry["path"]]
        project.exports.append(entry)
        self.save(project)

    def usage(self) -> dict[str, int]:
        """Small statistics shown on the dashboard."""
        projects = self.list()
        return {
            "projects": len(projects),
            "chapters": sum(p.chapter_count for p in projects),
            "words": sum(p.word_count for p in projects),
        }
