"""Text normalisation and sentence segmentation.

Speech-to-text output is noisy: no capitalisation, no punctuation guarantees,
run-on sentences and inconsistent whitespace.  These helpers turn that raw
transcript into predictable text before it is split into chapters.
"""

from __future__ import annotations

import re
import unicodedata

#: Words that end in a period but do not end a sentence.
_ABBREVIATIONS = {
    "mr", "mrs", "ms", "dr", "prof", "sr", "jr", "st", "mt", "rev",
    "gen", "col", "capt", "lt", "sgt", "vs", "etc", "al", "inc", "ltd",
    "co", "corp", "dept", "est", "fig", "no", "vol", "pp",
}

#: A sentence terminator plus the whitespace that follows it.
_SENTENCE_BOUNDARY = re.compile(r"([.!?]+)(\s+|$)")

#: Ellipsis used as a real sentence end.
_ELLIPSIS = re.compile(r"\.\.\.")

_WHITESPACE_RUN = re.compile(r"[ \t\f\v]+")
_BLANK_LINES = re.compile(r"\n{3,}")

#: Smart punctuation -> ASCII, applied so the text behaves predictably.
_PUNCTUATION_MAP = {
    "\u2018": "'", "\u2019": "'", "\u201a": "'", "\u201b": "'",
    "\u201c": '"', "\u201d": '"', "\u201e": '"',
    "\u2013": "-", "\u2014": "-", "\u2212": "-",
    "\u2026": "...", "\u00a0": " ",
}


def normalize_transcript(text: str) -> str:
    """Clean raw transcript text.

    Normalises unicode, folds smart punctuation to ASCII, collapses repeated
    whitespace and guarantees a single trailing newline is dropped.
    """
    if not text:
        return ""

    text = unicodedata.normalize("NFKC", text)
    for source, target in _PUNCTUATION_MAP.items():
        text = text.replace(source, target)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = _WHITESPACE_RUN.sub(" ", text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    text = _BLANK_LINES.sub("\n\n", text)
    return text.strip()


def _ends_with_abbreviation(chunk: str) -> bool:
    """True when ``chunk`` ends with an abbreviation such as "Mr." or "J."."""
    core = chunk.rstrip()
    while core and core[-1] in ".!?\"')":
        core = core[:-1]
    if not core:
        return False
    token = core.split()[-1]
    token = token.lower().strip("([\"'")
    if not token:
        return False
    if token in _ABBREVIATIONS:
        return True
    # Single-letter initials such as "J. R. R. Tolkien".
    return len(token) == 1 and token.isalpha()


def split_sentences(text: str) -> list[str]:
    """Split ``text`` into sentences.

    Abbreviations and initials are kept together, and ellipses are treated as
    a single terminator.  Empty fragments are discarded.
    """
    if not text or not text.strip():
        return []

    sentences: list[str] = []
    start = 0
    for match in _SENTENCE_BOUNDARY.finditer(text):
        chunk = text[start : match.end(1)]
        if not chunk.strip():
            start = match.end()
            continue
        if _ends_with_abbreviation(chunk):
            # Not a real sentence end - keep accumulating.
            continue
        sentences.append(chunk.strip())
        start = match.end()

    tail = text[start:].strip()
    if tail:
        sentences.append(tail)

    return [s for s in sentences if s]


def word_count(text: str) -> int:
    """Count whitespace separated words."""
    return len(text.split()) if text else 0


def estimate_reading_minutes(text: str, words_per_minute: int = 225) -> int:
    """Rough reading time for the given text."""
    return max(1, round(word_count(text) / max(1, words_per_minute)))


def truncate(text: str, limit: int = 280, suffix: str = "...") -> str:
    """Shorten ``text`` to ``limit`` characters on a word boundary."""
    text = (text or "").strip()
    if len(text) <= limit:
        return text
    cut = text[: max(0, limit - len(suffix))]
    if " " in cut:
        cut = cut[: cut.rfind(" ")]
    return cut.rstrip() + suffix
