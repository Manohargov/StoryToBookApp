"""Chapter splitting.

Two strategies are supported:

1. **Explicit markers** - when the speaker says "Chapter One" or "Chapter 3",
   the transcript is split exactly on those markers.
2. **Size based** - otherwise the transcript is grouped into chapters of
   roughly ``target_words`` words, always breaking on a sentence boundary so
   a chapter never starts mid-sentence.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .text import normalize_transcript, split_sentences, word_count

#: Matches spoken chapter markers such as "Chapter 3.", "Chapter One - The Forest".
_CHAPTER_MARKER = re.compile(
    r"(?:^|\n|(?<=[.!?]\s))\s*chapter\s+"
    r"(?P<number>\d{1,3}|[ivxlcdm]{1,7})\b"
    r"(?P<sep>[:.\-–]\s*)?"
    r"(?P<label>[^\n.!?]{0,80})"
    r"(?P<term>[.!?])?",
    re.IGNORECASE,
)

#: A chapter title longer than this many words is treated as body text.
_MAX_LABEL_WORDS = 6

_ROMAN = {
    "i": 1, "ii": 2, "iii": 3, "iv": 4, "v": 5, "vi": 6, "vii": 7,
    "viii": 8, "ix": 9, "x": 10, "xi": 11, "xii": 12, "xiii": 13,
    "xiv": 14, "xv": 15, "xvi": 16, "xvii": 17, "xviii": 18,
    "xix": 19, "xx": 20,
}


@dataclass
class Chapter:
    """A single chapter of a book."""

    title: str = ""
    text: str = ""
    words: int = field(default=0)

    def __post_init__(self) -> None:
        if not self.words:
            self.words = word_count(self.text)

    @property
    def word_count(self) -> int:
        return self.words or word_count(self.text)

    @property
    def preview(self) -> str:
        """First line of the chapter, useful for list views."""
        first_line = (self.text or "").strip().split("\n", 1)[0]
        return first_line[:120]

    def to_dict(self) -> dict:
        return {"title": self.title, "text": self.text, "words": self.words}

    @classmethod
    def from_dict(cls, data: dict) -> Chapter:
        return cls(
            title=data.get("title", ""),
            text=data.get("text", ""),
            words=int(data.get("words") or 0),
        )


def _marker_number(raw: str) -> int | None:
    raw = raw.strip().lower()
    if raw.isdigit():
        return int(raw)
    return _ROMAN.get(raw)


def detect_chapter_markers(text: str) -> list[dict]:
    """Find spoken chapter markers in a transcript.

    Returns a list of dictionaries with ``number``, ``label``, ``start`` and
    ``end`` offsets.  Markers whose number is not sequential are ignored
    because they are usually false positives from ordinary speech.
    """
    if not text:
        return []

    matches = []
    for match in _CHAPTER_MARKER.finditer(text):
        number = _marker_number(match.group("number"))
        if number is None:
            continue

        raw_label = (match.group("label") or "").strip(" .:-–")
        if len(raw_label.split()) > _MAX_LABEL_WORDS:
            # Too long to be a title - it belongs to the chapter body.
            label = ""
            end = match.start("label")
        else:
            label = raw_label
            end = match.end()

        matches.append(
            {
                "number": number,
                "label": label,
                "start": match.start(),
                "end": end,
            }
        )

    if len(matches) < 2:
        return []

    # Keep only a run of ascending markers - that filters out stray mentions.
    kept = [matches[0]]
    for candidate in matches[1:]:
        if candidate["number"] == kept[-1]["number"] + 1:
            kept.append(candidate)
    return kept if len(kept) >= 2 else []


def _title_for(number: int, label: str) -> str:
    label = (label or "").strip()
    if label:
        return f"Chapter {number}: {label}"
    return f"Chapter {number}"


def _split_on_markers(text: str, markers: list[dict]) -> list[Chapter]:
    chapters: list[Chapter] = []
    for index, marker in enumerate(markers):
        start = marker["end"]
        end = markers[index + 1]["start"] if index + 1 < len(markers) else len(text)
        body = text[start:end].strip()
        if not body:
            continue
        chapters.append(Chapter(title=_title_for(marker["number"], marker["label"]), text=body))
    return chapters

def _split_by_size(text: str, target_words: int) -> list[Chapter]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    if not paragraphs:
        paragraphs = [text]

    chapters: list[Chapter] = []
    # Each block is one paragraph of the book, stored as its sentences.
    blocks: list[list[str]] = []
    buffered_words = 0

    def flush() -> None:
        nonlocal blocks, buffered_words
        if not blocks:
            return
        body = "\n\n".join(" ".join(block).strip() for block in blocks if block).strip()
        if body:
            chapters.append(Chapter(title="", text=body))
        blocks = []
        buffered_words = 0

    for paragraph in paragraphs:
        sentences = split_sentences(paragraph)
        if not sentences:
            sentences = [paragraph]

        for sentence in sentences:
            sentence_words = word_count(sentence)
            # A single monster sentence still has to go somewhere.
            if sentence_words > target_words * 1.6:
                flush()
                words = sentence.split()
                for start in range(0, len(words), target_words):
                    chunk = " ".join(words[start : start + target_words])
                    chapters.append(Chapter(title="", text=chunk))
                continue

            if buffered_words and buffered_words + sentence_words > target_words:
                flush()
            blocks.append([sentence])
            buffered_words += sentence_words

    flush()

    # Merge a tiny trailing chapter back into the previous one.
    if len(chapters) > 1 and chapters[-1].word_count < max(40, target_words // 8):
        tail = chapters.pop()
        chapters[-1].text = f"{chapters[-1].text}\n\n{tail.text}".strip()
        chapters[-1].words = word_count(chapters[-1].text)

    for index, chapter in enumerate(chapters, start=1):
        if not chapter.title:
            chapter.title = f"Chapter {index}"
    return chapters


def format_transcript(text: str) -> str:
    """Lay the transcript out for reading.

    Chapter markers are moved onto their own line and paragraphs are kept
    apart, so the editor and the rendered book both read cleanly.
    """
    cleaned = normalize_transcript(text)
    if not cleaned:
        return ""

    markers = detect_chapter_markers(cleaned)
    if not markers:
        return cleaned

    pieces: list[str] = []
    last = 0
    for marker in markers:
        head = cleaned[last : marker["start"]].strip()
        if head:
            pieces.append(head)
        pieces.append(cleaned[marker["start"] : marker["end"]].strip())
        last = marker["end"]
    tail = cleaned[last:].strip()
    if tail:
        pieces.append(tail)

    return "\n\n".join(piece for piece in pieces if piece)


def build_chapters(text: str, target_words: int = 1000) -> list[Chapter]:
    """Split a transcript into chapters.

    Explicit "Chapter N" markers win; otherwise the text is chunked by size.
    Returns an empty list for empty input.
    """
    cleaned = normalize_transcript(text)
    if not cleaned:
        return []

    markers = detect_chapter_markers(cleaned)
    if markers:
        chapters = _split_on_markers(cleaned, markers)
        if chapters:
            return chapters

    return _split_by_size(cleaned, max(100, target_words))
