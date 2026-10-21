"""Transcription providers."""

from __future__ import annotations

from .base import (
    TranscriptionProvider,
    TranscriptionResult,
    TranscriptionSegment,
)
from .openai_api import OpenAITranscriptionProvider
from .whisper_local import WhisperLocalProvider

__all__ = [
    "OpenAITranscriptionProvider",
    "TranscriptionProvider",
    "TranscriptionResult",
    "TranscriptionSegment",
    "WhisperLocalProvider",
]

_REGISTRY: dict[str, type[TranscriptionProvider]] = {
    WhisperLocalProvider.name: WhisperLocalProvider,
    OpenAITranscriptionProvider.name: OpenAITranscriptionProvider,
}

#: Providers offered in the Settings screen, in display order.
CHOICES: list[str] = ["whisper_local", "openai_api"]


def list_transcription_providers() -> list[TranscriptionProvider]:
    """Instantiate every known provider."""
    return [_REGISTRY[name]() for name in CHOICES if name in _REGISTRY]


def build_transcription_provider(name: str, settings) -> TranscriptionProvider:
    """Return the provider registered under ``name``.

    Falls back to the local Whisper provider when the name is unknown, and
    transparently swaps in a provider that actually works when the requested
    one has no dependencies installed.
    """
    provider_cls = _REGISTRY.get(name) or _REGISTRY["whisper_local"]
    provider = provider_cls(settings)
    if provider.is_available():
        return provider

    for fallback_name in CHOICES:
        fallback_cls = _REGISTRY.get(fallback_name)
        if fallback_cls is None:
            continue
        fallback = fallback_cls(settings)
        if fallback.is_available():
            return fallback
    return provider
