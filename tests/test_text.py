"""Tests for the text utilities."""

from __future__ import annotations

from storytobook.domain.text import (
    estimate_reading_minutes,
    normalize_transcript,
    split_sentences,
    truncate,
    word_count,
)


class TestNormalize:
    def test_collapses_whitespace(self):
        assert normalize_transcript("  hello   world  ") == "hello world"

    def test_folds_smart_punctuation(self):
        assert normalize_transcript("“quoted” it’s fine") == '"quoted" it\'s fine'

    def test_collapses_blank_lines(self):
        assert normalize_transcript("a\n\n\n\nb") == "a\n\nb"

    def test_empty_input(self):
        assert normalize_transcript("") == ""
        assert normalize_transcript(None) == ""


class TestSplitSentences:
    def test_simple_split(self):
        assert split_sentences("One. Two! Three?") == ["One.", "Two!", "Three?"]

    def test_keeps_abbreviations_together(self):
        assert split_sentences("Dr. Smith arrived. He was late.") == [
            "Dr. Smith arrived.",
            "He was late.",
        ]

    def test_keeps_initials_together(self):
        assert split_sentences("J. R. R. Tolkien wrote books.") == [
            "J. R. R. Tolkien wrote books."
        ]

    def test_ignores_trailing_whitespace_only(self):
        assert split_sentences("   ") == []

    def test_sentence_without_terminator(self):
        assert split_sentences("no full stop here") == ["no full stop here"]


class TestHelpers:
    def test_word_count(self):
        assert word_count("one two three") == 3
        assert word_count("") == 0

    def test_reading_minutes(self):
        assert estimate_reading_minutes("word " * 450) == 2

    def test_truncate(self):
        assert truncate("short", 10) == "short"
        assert len(truncate("word " * 50, 30)) <= 30
        assert truncate("word " * 50, 30).endswith("...")
