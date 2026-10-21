"""End to end test: from a blank project to a finished book."""

from __future__ import annotations

from storytobook.domain.project import ProjectStatus
from storytobook.exporters.base import BookDocument
from storytobook.services.pipeline import BookPipeline

from .conftest import SAMPLE_TEXT


def test_project_becomes_a_book(library, settings):
    settings.cover_provider = "pillow"
    pipeline = BookPipeline(library, settings)

    project = library.create(title="The Turning Tide")
    project.author = "Maren Vale"
    project.publisher = "Harbourlight Books"
    project.acknowledgment = "For the readers of my first book."
    project.author_note = "Spoken aloud first, typed out by hand."

    # 1. The transcript arrives (normally from Whisper).
    project.transcript = SAMPLE_TEXT
    library.save(project)

    # 2. It is split into chapters.
    chapters = pipeline.split_chapters(project)
    assert len(chapters) == 5
    assert chapters[0].title == "Chapter 1: The Crossing"

    # 3. A cover is drawn.
    cover_path = pipeline.generate_cover(project)
    assert cover_path.exists()
    assert cover_path.suffix == ".png"

    # 4. The book is published.
    pdf_path = pipeline.export(project, "pdf")
    assert pdf_path.exists()
    assert pdf_path.read_bytes().startswith(b"%PDF")

    # 5. The project remembers everything.
    stored = library.load(project.id)
    assert stored.status is ProjectStatus.EXPORTED
    assert stored.cover_filename == "cover.png"
    assert stored.exports
    assert stored.exports[0]["format"] == "pdf"
    assert len(stored.chapters) == 5


def test_every_format_can_be_published(library, settings):
    settings.cover_provider = "pillow"
    pipeline = BookPipeline(library, settings)

    project = library.create(title="Formats")
    project.transcript = SAMPLE_TEXT
    pipeline.split_chapters(project)
    pipeline.generate_cover(project)

    produced = {}
    for export_format in ("pdf", "epub", "html"):
        path = pipeline.export(project, export_format)
        produced[export_format] = path
        assert path.exists()
        assert path.stat().st_size > 500

    assert produced["pdf"].suffix == ".pdf"
    assert produced["epub"].suffix == ".epub"
    assert produced["html"].suffix == ".html"


def test_a_book_can_be_built_without_a_cover(library, settings):
    pipeline = BookPipeline(library, settings)

    project = library.create(title="No Cover")
    project.transcript = SAMPLE_TEXT
    pipeline.split_chapters(project)

    path = pipeline.export(project, "pdf")
    assert path.exists()


def test_the_document_snapshot_matches_the_project(library):
    project = library.create(title="Snapshot")
    project.author = "Ada"
    project.transcript = SAMPLE_TEXT
    library.save(project)

    document = BookDocument.from_project(project)
    assert document.title == "Snapshot"
    assert document.author == "Ada"
    assert document.full_text == SAMPLE_TEXT


def test_a_manually_typed_story_needs_no_audio(library, settings):
    """A user may type the story instead of recording it."""
    pipeline = BookPipeline(library, settings)

    project = library.create(title="Typed By Hand")
    project.transcript = "Chapter 1 Only. A short story written by hand."
    library.save(project)

    chapters = pipeline.split_chapters(project)
    assert len(chapters) == 1
    assert not library.audio_path(project.id).exists()

    path = pipeline.export(project, "html")
    assert path.exists()
    assert "A short story written by hand." in path.read_text("utf-8")
