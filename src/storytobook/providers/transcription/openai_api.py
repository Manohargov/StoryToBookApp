"""Transcription through the OpenAI audio API."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from ...errors import ProviderError, ProviderUnavailableError
from .base import ProgressCallback, TranscriptionProvider, TranscriptionResult

_INSTALL_HINT = "Install it with:  pip install openai  (and set an API key)"


class OpenAITranscriptionProvider(TranscriptionProvider):
    """Sends the recording to OpenAI's speech-to-text endpoint."""

    name = "openai_api"
    label = "OpenAI API (cloud)"
    requirements = "Needs the 'openai' package and an API key"

    def __init__(self, settings=None) -> None:
        super().__init__(settings)
        self._client = None

    def _api_key(self) -> str:
        return (getattr(self.settings, "openai_api_key", "") or "").strip()

    def is_available(self) -> bool:
        if importlib.util.find_spec("openai") is None:
            return False
        return bool(self._api_key())

    def _get_client(self):
        if self._client is not None:
            return self._client
        if importlib.util.find_spec("openai") is None:
            raise ProviderUnavailableError(
                "The 'openai' package is not installed.", _INSTALL_HINT
            )
        try:
            from openai import OpenAI  # noqa: PLC0415 - optional dependency

            self._client = OpenAI(api_key=self._api_key())
        except Exception as exc:
            raise ProviderError(f"Could not create the OpenAI client: {exc}") from exc
        return self._client

    def transcribe(
        self, audio_path: Path, progress: ProgressCallback | None = None
    ) -> TranscriptionResult:
        path = Path(audio_path)
        if not path.exists():
            raise ProviderError(f"Audio file not found: {path}")

        client = self._get_client()
        model = getattr(self.settings, "openai_transcription_model", "whisper-1") or "whisper-1"

        if progress:
            progress(f"Uploading audio to OpenAI ({model})...")

        try:
            with path.open("rb") as handle:
                response = client.audio.transcriptions.create(model=model, file=handle)
        except Exception as exc:
            raise ProviderError(f"OpenAI transcription failed: {exc}") from exc

        text = getattr(response, "text", None)
        if text is None and isinstance(response, dict):
            text = response.get("text", "")

        return TranscriptionResult(text=(text or "").strip(), provider=self.name)
