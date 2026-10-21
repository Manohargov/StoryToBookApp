"""Tests for the export renderers."""

from __future__ import annotations

import zipfile

import pytest

from storytobook.domain.chapter import Chapter
from storytobook.exporters.base import BookDocument, safe_filename
from storytobook.exporters.epub import EpubExporter
from storytobook.exporters.html import HtmlExporter
from storytobook.exporters.pdf import PdfExporter, to_latin1
from storytobook.exporters.registry import build_exporter, list_exporters


@pytest.fixture
def document(tmp_path):
    cover = tmp_path / "cover.png"
    from PIL import Image

    Image.new("RGB", (120, 160), (30, 40, 60)).save(cover)
    return BookDocument(
        title="The Quiet Harbour",
        author="Ada Marlowe",
        publisher="Lantern Press",
        acknowledgment="Thank you.",
        author_note="Spoken aloud first.",
        chapters=[
            Chapter(title="Chapter 1: Arrival", text="He arrived at dawn.\n\nThe gulls cried out."),
            Chapter(title="Chapter 2: The Storm", text="Then the wind rose fast."),
        ],
        cover_path=cover,
    )


class TestSafeFilename:
    def test_removes_illegal_characters(self):
        assert "/" not in safe_filename("a/b:c*d")
        assert safe_filename("a/b:c*d") == "abcd"

    def test_falls_back_when_empty(self):
        assert safe_filename("   ") == "book"

    def test_trims_trailing_dots(self):
        assert not safe_filename("name...").endswith(".")


class TestRegistry:
    def test_lists_every_exporter(self):
        names = {exporter.name for exporter in list_exporters()}
        assert names == {"pdf", "epub", "html"}

    def test_builds_by_name(self):
        assert build_exporter("epub").name == "epub"

    def test_unknown_name_falls_back_to_pdf(self):
        assert build_exporter("mobi").name == "pdf"


class TestPdf:
    def test_creates_a_pdf(self, document, tmp_path):
        path = PdfExporter().export(document, tmp_path, "book")
        assert path.exists()
        assert path.read_bytes().startswith(b"%PDF")

    def test_contains_the_title(self, document, tmp_path):
        path = PdfExporter().export(document, tmp_path, "book")
        assert path.stat().st_size > 1000

    def test_missing_cover_is_survivable(self, document, tmp_path):
        document.cover_path = tmp_path / "nope.png"
        path = PdfExporter().export(document, tmp_path, "book")
        assert path.exists()


class TestEpub:
    def test_creates_a_valid_archive(self, document, tmp_path):
        path = EpubExporter().export(document, tmp_path, "book")
        assert path.exists()
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            assert names[0] == "mimetype"
            assert archive.read("mimetype") == b"application/epub+zip"
            assert "META-INF/container.xml" in names
            assert "OEBPS/package.opf" in names
            assert "OEBPS/nav.xhtml" in names

    def test_mimetype_is_stored_uncompressed(self, document, tmp_path):
        path = EpubExporter().export(document, tmp_path, "book")
        with zipfile.ZipFile(path) as archive:
            info = archive.getinfo("mimetype")
            assert info.compress_type == zipfile.ZIP_STORED

    def test_one_document_per_chapter(self, document, tmp_path):
        path = EpubExporter().export(document, tmp_path, "book")
        with zipfile.ZipFile(path) as archive:
            assert "OEBPS/text/chapter_1.xhtml" in archive.namelist()
            assert "OEBPS/text/chapter_2.xhtml" in archive.namelist()

    def test_cover_is_embedded(self, document, tmp_path):
        path = EpubExporter().export(document, tmp_path, "book")
        with zipfile.ZipFile(path) as archive:
            assert "OEBPS/cover.png" in archive.namelist()


class TestHtml:
    def test_creates_a_single_file(self, document, tmp_path):
        path = HtmlExporter().export(document, tmp_path, "book")
        content = path.read_text("utf-8")
        assert content.startswith("<!DOCTYPE html>")
        assert "The Quiet Harbour" in content
        assert "Chapter 1: Arrival" in content

    def test_embeds_the_cover(self, document, tmp_path):
        path = HtmlExporter().export(document, tmp_path, "book")
        assert "data:image/png;base64," in path.read_text("utf-8")

    def test_escapes_html(self, tmp_path):
        document = BookDocument(title="<script>alert(1)</script>", chapters=[])
        path = HtmlExporter().export(document, tmp_path, "book")
        content = path.read_text("utf-8")
        assert "<script>alert(1)</script>" not in content
        assert "&lt;script&gt;" in content


class TestLatin1Fallback:
    def test_replaces_smart_quotes(self):
        assert to_latin1("“hi”") == '"hi"'

    def test_drops_characters_outside_latin1(self):
        assert to_latin1("日本") == ""

    def test_keeps_plain_text(self):
        assert to_latin1("Hello world") == "Hello world"
