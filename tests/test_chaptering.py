"""Tests for chapter detection and splitting."""

from __future__ import annotations

from storytobook.domain.chapter import (
    build_chapters,
    detect_chapter_markers,
    format_transcript,
)

from .conftest import SAMPLE_TEXT


class TestMarkerDetection:
    def test_finds_numbered_markers(self):
        markers = detect_chapter_markers(SAMPLE_TEXT)
        assert [m["number"] for m in markers] == [1, 2, 3, 4, 5]

    def test_captures_labels(self):
        markers = detect_chapter_markers(SAMPLE_TEXT)
        assert markers[0]["label"] == "The Crossing"
        assert markers[2]["label"] == "The House"

    def test_ignores_a_single_mention(self):
        assert detect_chapter_markers("In chapter 4 they left.") == []

    def test_ignores_non_sequential_numbers(self):
        text = "Chapter 7 begins. Chapter 9 begins. Chapter 2 begins."
        assert detect_chapter_markers(text) == []

    def test_handles_roman_numerals(self):
        text = "Chapter I. First. Chapter II. Second."
        markers = detect_chapter_markers(text)
        assert [m["number"] for m in markers] == [1, 2]


class TestBuildChapters:
    def test_splits_on_explicit_markers(self):
        chapters = build_chapters(SAMPLE_TEXT)
        assert len(chapters) == 5
        assert chapters[0].title == "Chapter 1: The Crossing"
        assert chapters[-1].title == "Chapter 5: The Turning"

    def test_marker_text_is_not_duplicated_in_the_body(self):
        chapters = build_chapters(SAMPLE_TEXT)
        assert "Chapter 1 The Crossing" not in chapters[0].text

    def test_falls_back_to_size_based_splitting(self):
        text = " ".join(["word"] * 2500)
        chapters = build_chapters(text, target_words=500)
        assert len(chapters) == 5
        assert all(chapter.title.startswith("Chapter") for chapter in chapters)
        assert all(chapter.word_count <= 520 for chapter in chapters)

    def test_breaks_on_sentence_boundaries(self):
        text = "This is a sentence. " * 200
        chapters = build_chapters(text, target_words=50)
        for chapter in chapters:
            assert chapter.text.strip().endswith(".")

    def test_paragraph_breaks_are_preserved(self):
        text = "First paragraph here. Second sentence.\n\nNew paragraph starts."
        chapters = build_chapters(text, target_words=100)
        assert "\n\n" in chapters[0].text

    def test_empty_text(self):
        assert build_chapters("") == []
        assert build_chapters("   ") == []

    def test_very_long_single_sentence_is_split(self):
        text = " ".join(["word"] * 2000)
        chapters = build_chapters(text, target_words=100)
        assert len(chapters) > 1

    def test_tiny_trailing_chapter_is_merged(self):
        text = " ".join(["word"] * 520) + " end."
        chapters = build_chapters(text, target_words=500)
        assert all(chapter.word_count >= 40 for chapter in chapters)


class TestFormatTranscript:
    def test_moves_markers_onto_their_own_line(self):
        formatted = format_transcript(SAMPLE_TEXT)
        assert "Chapter 1 The Crossing.\n" in formatted

    def test_is_idempotent(self):
        once = format_transcript(SAMPLE_TEXT)
        assert format_transcript(once) == once

    def test_leaves_text_without_markers_alone(self):
        text = "A story without chapters."
        assert format_transcript(text) == text

    def test_empty_input(self):
        assert format_transcript("") == ""
