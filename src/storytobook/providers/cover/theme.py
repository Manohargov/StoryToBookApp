"""Story genre detection and prompt construction."""

from __future__ import annotations

import re

#: Genre keyword table.  The first list is matched against the story text,
#: the second one is used to build the image prompt.
GENRES: dict[str, dict] = {
    "fantasy": {
        "keywords": [
            "magic", "dragon", "kingdom", "wizard", "witch", "quest", "sword",
            "sorcer", "enchant", "elf", "dwarf", "myth", "spell", "realm",
        ],
        "prompt": "epic fantasy illustration, mystical kingdom, ancient magic, dramatic sky",
        "palette": ((24, 20, 58), (92, 48, 140), (214, 168, 96)),
    },
    "science fiction": {
        "keywords": [
            "space", "future", "robot", "starship", "galaxy", "planet", "orbit",
            "android", "colony", "laser", "alien", "cyber", "machine", "crew",
        ],
        "prompt": "science fiction concept art, deep space, sleek technology, nebula backdrop",
        "palette": ((8, 18, 44), (30, 84, 160), (108, 220, 255)),
    },
    "mystery": {
        "keywords": [
            "detective", "crime", "secret", "shadow", "clue", "murder", "mystery",
            "suspect", "evidence", "vanish", "stolen", "alibi",
        ],
        "prompt": "mystery noir illustration, rain slick street, dramatic shadows, moody atmosphere",
        "palette": ((12, 14, 22), (48, 52, 68), (188, 168, 120)),
    },
    "romance": {
        "keywords": [
            "love", "heart", "kiss", "passion", "wedding", "romance", "beloved",
            "embrace", "heartbeat", "courtship",
        ],
        "prompt": "romantic painterly illustration, warm golden light, soft bokeh, tender mood",
        "palette": ((46, 16, 32), (168, 62, 84), (244, 196, 168)),
    },
    "horror": {
        "keywords": [
            "dark", "fear", "ghost", "blood", "nightmare", "haunt", "terrify",
            "demon", "scream", "cursed", "shadow", "rot",
        ],
        "prompt": "horror illustration, ominous fog, harsh rim light, unsettling mood",
        "palette": ((10, 8, 14), (58, 16, 26), (188, 60, 52)),
    },
    "adventure": {
        "keywords": [
            "journey", "treasure", "mountain", "ocean", "explore", "island",
            "ship", "voyage", "river", "valley", "map", "compass",
        ],
        "prompt": "adventure illustration, sweeping landscape, golden hour, distant horizon",
        "palette": ((18, 40, 44), (58, 122, 92), (232, 208, 148)),
    },
    "history": {
        "keywords": [
            "century", "empire", "king", "queen", "battle", "castle", "war",
            "dynasty", "knight", "soldier", "reign", "crusade",
        ],
        "prompt": "historical illustration, aged parchment tones, dramatic period detail, oil painting",
        "palette": ((36, 28, 18), (116, 84, 46), (222, 196, 142)),
    },
    "literary": {
        "keywords": [
            "mother", "father", "family", "home", "town", "school", "friend",
            "childhood", "winter", "summer", "village", "letter",
        ],
        "prompt": "literary fiction illustration, soft natural light, nostalgic atmosphere, muted palette",
        "palette": ((30, 34, 38), (96, 106, 116), (216, 210, 196)),
    },
}

#: Used when nothing in the text matches a known genre.
DEFAULT_GENRE = "literary"

#: Frequent words are ignored when scoring a genre.
_STOPWORDS = {
    "the", "and", "that", "have", "for", "not", "with", "you", "this", "but",
    "his", "from", "they", "say", "her", "she", "will", "one", "all", "would",
    "there", "their", "what", "out", "about", "who", "get", "which", "when",
    "make", "like", "into", "your", "some", "them", "than", "then", "now",
    "was", "were", "are", "been", "had", "has", "did", "does", "could", "should",
}


def detect_genre(text: str) -> tuple[str, list[str]]:
    """Guess the genre of a story.

    Returns the genre name and the keywords that triggered it.
    """
    if not text:
        return DEFAULT_GENRE, []

    words = re.findall(r"[a-z']+", text.lower())
    if not words:
        return DEFAULT_GENRE, []

    counts = {word: 0 for word in set(words) if word not in _STOPWORDS}
    for word in words:
        if word in counts:
            counts[word] += 1

    best_genre = DEFAULT_GENRE
    best_score = 0
    best_hits: list[str] = []

    for genre, spec in GENRES.items():
        score = 0
        hits: list[str] = []
        for keyword in spec["keywords"]:
            hits_in_text = counts.get(keyword, 0)
            if hits_in_text:
                score += hits_in_text
                hits.append(keyword)
        if score > best_score:
            best_genre = genre
            best_score = score
            best_hits = hits

    if best_score == 0:
        return DEFAULT_GENRE, []
    return best_genre, sorted(best_hits, key=lambda k: -counts.get(k, 0))[:6]


def palette_for(genre: str) -> tuple[tuple[int, int, int], ...]:
    """Colour palette used by the procedural cover renderer."""
    return GENRES.get(genre, GENRES[DEFAULT_GENRE])["palette"]


def build_prompt(genre: str, title: str = "", author: str = "", extra: str = "") -> str:
    """Compose the image prompt for a genre."""
    spec = GENRES.get(genre, GENRES[DEFAULT_GENRE])
    parts = [
        "book cover illustration",
        spec["prompt"],
        "cinematic lighting, highly detailed, painterly, atmospheric",
    ]
    if title:
        parts.append(f"thematic of '{title}'")
    if extra:
        parts.append(extra.strip())
    return ", ".join(part for part in parts if part)


def negative_prompt() -> str:
    """Standard negative prompt shared by the diffusion providers."""
    return (
        "blurry, low quality, distorted, ugly, bad anatomy, deformed, watermark, "
        "signature, text, letters, logo, frame, border"
    )
