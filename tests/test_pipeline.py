"""Tests for the transcription providers and the pipeline."""

from __future__ import annotations

import pytest

from storytobook.domain.project import ProjectStatus
from storytobook.providers.transcription.base import TranscriptionResult, TranscriptionSegment
from storytobook.providers.transcription.openai_api import OpenAITranscriptionProvider
from storytobook.providers.transcription.whisper_local import WhisperLocalProvider
from storytobook.services.pipeline import BookPipeline, Stage


class TestTranscriptionProviders:
    def test_whisper_reports_availability(self):
        assert isinstance(WhisperLocalProvider().is_available(), bool)

    def test_whisper_rejects_a_missing_file(self):
        provider = WhisperLocalProvider()
        if provider.is_available():
            from storytobook.errors import ProviderError

            with pytest.raises(ProviderError):
                provider.transcribe("does-not-exist.wav")

    def test_openai_requires_a_key(self, settings):
        settings.openai_api_key = ""
        assert OpenAITranscriptionProvider(settings).is_available() is False

    def test_fallback_picks_something_usable(self, settings):
        from storytobook.providers.transcription import build_transcription_provider

        provider = build_transcription_provider("nonsense", settings)
        assert provider.name in {"whisper_local", "openai_api"}

    def test_result_helpers(self):
        result = TranscriptionResult(
            text="hello",
            segments=[TranscriptionSegment(0, 1.5, "hello"), TranscriptionSegment(1.5, 3, "there")],
        )
        assert result.duration == 3.0


class TestPipeline:
    def test_split_chapters_stores_the_transcript(self, library, settings, project):
        pipeline = BookPipeline(library, settings)
        project.transcript = (
            "Chapter 1 Start. The hero set out. "
            "Chapter 2 Middle. The journey grew hard. "
            "Chapter 3 End. The hero came home."
        )
        chapters = pipeline.split_chapters(project)

        assert len(chapters) == 3
        assert project.chapter_count == 3
        assert project.status is ProjectStatus.TRANSCRIBED
        assert library.load(project.id).chapter_count == 3

    def test_split_chapters_formats_the_transcript(self, library, settings, project):
        pipeline = BookPipeline(library, settings)
        project.transcript = "Chapter 1 Start. Text. Chapter 2 Next. More text."
        pipeline.split_chapters(project)
        assert "Chapter 1 Start.\n" in project.transcript

    def test_generate_cover_writes_the_image(self, library, settings, project):
        pipeline = BookPipeline(library, settings)
        settings.cover_provider = "pillow"
        project.transcript = "A story about a dragon and a magic kingdom."
        project.title = "Dragon Road"
        project.author = "Ada"

        path = pipeline.generate_cover(project)
        assert path.exists()
        assert path == library.cover_path(project.id)
        assert project.status is ProjectStatus.ILLUSTRATED

    def test_export_writes_the_book(self, library, settings, project):
        pipeline = BookPipeline(library, settings)
        project.transcript = "Chapter 1 Start. Some text here. Chapter 2 End. More text."
        pipeline.split_chapters(project)
        settings.cover_provider = "pillow"
        pipeline.generate_cover(project)

        path = pipeline.export(project, "pdf")
        assert path.exists()
        assert path.suffix == ".pdf"
        assert project.status is ProjectStatus.EXPORTED
        assert library.load(project.id).exports

    def test_export_works_without_a_cover(self, library, settings, project):
        pipeline = BookPipeline(library, settings)
        project.transcript = "Chapter 1 Start. Some text. Chapter 2 End. More text."
        pipeline.split_chapters(project)
        path = pipeline.export(project, "html")
        assert path.exists()

    def test_run_reports_progress(self, library, settings, project):
        pipeline = BookPipeline(library, settings)
        settings.cover_provider = "pillow"
        project.transcript = "Chapter 1 Start. Text. Chapter 2 End. More text."

        events = []
        pipeline.run(project, [Stage.CHAPTERS, Stage.COVER], events.append)

        assert events
        assert all(hasattr(event, "stage") for event in events)
        assert events[-1].stage is Stage.DONE

    def test_run_reports_a_failure(self, library, settings, project):
        pipeline = BookPipeline(library, settings)
        # There is no recording, so transcription cannot run.
        events = []
        with pytest.raises(FileNotFoundError):
            pipeline.run(project, [Stage.TRANSCRIBE], events.append)

        assert any(event.stage is Stage.FAILED for event in events)

    def test_transcribe_without_audio(self, library, settings, project):
        pipeline = BookPipeline(library, settings)
        with pytest.raises(FileNotFoundError):
            pipeline.transcribe(project)
