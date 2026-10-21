"""Pluggable providers for transcription and cover art.

Every provider implements a small protocol and reports whether it is
available.  The UI uses that to show honest status messages instead of
failing at the last moment.
"""

from .cover import (
    CoverProvider,
    CoverRequest,
    CoverResult,
    build_cover_provider,
    list_cover_providers,
)
from .transcription import (
    TranscriptionProvider,
    TranscriptionResult,
    TranscriptionSegment,
    build_transcription_provider,
    list_transcription_providers,
)

__all__ = [
    "CoverProvider",
    "CoverRequest",
    "CoverResult",
    "TranscriptionProvider",
    "TranscriptionResult",
    "TranscriptionSegment",
    "build_cover_provider",
    "build_transcription_provider",
    "list_cover_providers",
    "list_transcription_providers",
]
