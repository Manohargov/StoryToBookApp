"""Orchestration of the record -> book pipeline.

Every step runs on a worker thread and reports progress through a callback.
The interface polls a queue so the UI thread is never blocked.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from ..domain.chapter import Chapter, build_chapters, format_transcript
from ..domain.project import Project, ProjectStatus
from ..domain.text import normalize_transcript
from ..exporters.base import BookDocument, safe_filename
from ..exporters.registry import build_exporter
from ..providers.cover import CoverRequest, build_cover_provider
from ..providers.transcription import build_transcription_provider
from .library import Library


class Stage(str, Enum):
    """The stages a project moves through."""

    TRANSCRIBE = "transcribe"
    CHAPTERS = "chapters"
    COVER = "cover"
    EXPORT = "export"
    DONE = "done"
    FAILED = "failed"


@dataclass
class Progress:
    """A progress update emitted by the pipeline."""

    stage: Stage = Stage.DONE
    message: str = ""
    percent: float = 0.0
    error: str = ""
    detail: str = ""
    result: object | None = field(default=None, compare=False)

    @property
    def failed(self) -> bool:
        return self.stage is Stage.FAILED


ProgressCallback = Callable[[Progress], None]


class BookPipeline:
    """Runs the individual steps that turn a recording into a book."""

    def __init__(self, library: Library, settings) -> None:
        self.library = library
        self.settings = settings

    # ------------------------------------------------------------------ #
    # Steps
    # ------------------------------------------------------------------ #
    def transcribe(self, project: Project, progress: ProgressCallback | None = None) -> str:
        """Transcribe the project audio and store the text."""
        audio_path = self.library.audio_path(project.id)
        if not audio_path.exists():
            raise FileNotFoundError(
                "No recording was found for this project. Record or import audio first."
            )

        provider = build_transcription_provider(self.settings.transcription_provider, self.settings)

        def on_detail(message: str) -> None:
            if progress:
                progress(Progress(stage=Stage.TRANSCRIBE, message=message, percent=0.35))

        result = provider.transcribe(audio_path, on_detail)
        text = normalize_transcript(result.text)
        if not text:
            raise RuntimeError("The transcription came back empty. Try recording again.")

        project.transcript = text
        project.audio_filename = "source.wav"
        project.status = ProjectStatus.TRANSCRIBED
        self.library.save(project)

        if progress:
            progress(
                Progress(
                    stage=Stage.TRANSCRIBE,
                    message="Transcript ready",
                    percent=1.0,
                    detail=f"{len(text.split())} words",
                    result=text,
                )
            )
        return text

    def split_chapters(self, project: Project, progress: ProgressCallback | None = None) -> list[Chapter]:
        """Split the transcript into chapters and store them."""
        project.transcript = format_transcript(project.transcript)
        chapters = build_chapters(project.transcript, self.settings.chapter_target_words)
        project.chapters = chapters
        if project.status in {ProjectStatus.DRAFT, ProjectStatus.RECORDED}:
            project.status = ProjectStatus.TRANSCRIBED
        self.library.save(project)

        if progress:
            progress(
                Progress(
                    stage=Stage.CHAPTERS,
                    message=f"{len(chapters)} chapters ready",
                    percent=1.0,
                    result=chapters,
                )
            )
        return chapters

    def generate_cover(self, project: Project, progress: ProgressCallback | None = None) -> Path:
        """Render the cover image and store it next to the project."""
        provider = build_cover_provider(self.settings.cover_provider, self.settings)
        cover_path = self.library.cover_path(project.id)

        request = CoverRequest(
            story_text=project.transcript,
            title=project.display_name,
            author=project.author,
            output_path=cover_path,
            width=self.settings.cover_width,
            height=self.settings.cover_height,
            steps=self.settings.cover_steps,
            guidance_scale=self.settings.cover_guidance_scale,
            seed=self.settings.cover_seed,
            extra_prompt=self.settings.cover_extra_prompt,
        )

        def on_detail(message: str) -> None:
            if progress:
                progress(Progress(stage=Stage.COVER, message=message, percent=0.4))

        result = provider.generate(request, on_detail)
        project.cover_filename = cover_path.name
        if project.status in {
            ProjectStatus.DRAFT,
            ProjectStatus.RECORDED,
            ProjectStatus.TRANSCRIBED,
        }:
            project.status = ProjectStatus.ILLUSTRATED
        self.library.save(project)

        if progress:
            progress(
                Progress(
                    stage=Stage.COVER,
                    message="Cover ready",
                    percent=1.0,
                    detail=result.prompt,
                    result=result,
                )
            )
        return result.path

    def export(
        self, project: Project, export_format: str = "pdf", progress: ProgressCallback | None = None
    ) -> Path:
        """Render the book to a file inside the project's export folder."""
        exporter = build_exporter(export_format)
        document = BookDocument.from_project(project, self.library.cover_path(project.id))
        if not document.chapters and project.transcript:
            document.chapters = build_chapters(
                project.transcript, self.settings.chapter_target_words
            )

        stem = safe_filename(project.display_name, "book")
        output_dir = self.library.exports_dir(project.id)

        if progress:
            progress(
                Progress(
                    stage=Stage.EXPORT,
                    message=f"Building the {exporter.label}...",
                    percent=0.5,
                )
            )

        output_path = exporter.export(document, output_dir, stem)
        self.library.record_export(project, output_path, exporter.name)
        project.status = ProjectStatus.EXPORTED
        self.library.save(project)

        if progress:
            progress(
                Progress(
                    stage=Stage.EXPORT,
                    message=f"{exporter.label} ready",
                    percent=1.0,
                    detail=str(output_path),
                    result=output_path,
                )
            )
        return output_path

    # ------------------------------------------------------------------ #
    def run(
        self,
        project: Project,
        stages: Iterable[str] = (),
        progress: ProgressCallback | None = None,
    ) -> None:
        """Run several steps in sequence, reporting progress for each."""
        stages = list(stages) or [Stage.TRANSCRIBE, Stage.CHAPTERS, Stage.COVER]
        weights = {Stage.TRANSCRIBE: 0.55, Stage.CHAPTERS: 0.15, Stage.COVER: 0.3}
        total = sum(weights.get(Stage(s), 0.1) for s in stages) or 1.0
        consumed = 0.0

        try:
            for stage in stages:
                stage = Stage(stage)
                if progress:
                    progress(
                        Progress(stage=stage, message=self._start_message(stage), percent=consumed / total)
                    )

                if stage is Stage.TRANSCRIBE:
                    self.transcribe(project, progress)
                elif stage is Stage.CHAPTERS:
                    self.split_chapters(project, progress)
                elif stage is Stage.COVER:
                    self.generate_cover(project, progress)
                elif stage is Stage.EXPORT:
                    self.export(project, self.settings.default_export_format, progress)

                consumed += weights.get(stage, 0.1)
                if progress:
                    progress(Progress(stage=stage, message="done", percent=consumed / total))
        except Exception as exc:
            if progress:
                progress(
                    Progress(stage=Stage.FAILED, message="Something went wrong", percent=1.0, error=str(exc))
                )
            raise

        if progress:
            progress(Progress(stage=Stage.DONE, message="Finished", percent=1.0))

    @staticmethod
    def _start_message(stage: Stage) -> str:
        return {
            Stage.TRANSCRIBE: "Transcribing audio...",
            Stage.CHAPTERS: "Splitting into chapters...",
            Stage.COVER: "Creating the cover...",
            Stage.EXPORT: "Building your book...",
        }.get(stage, "Working...")
