"""Local Whisper transcription via the ``openai-whisper`` package."""

from __future__ import annotations

import importlib.util
from pathlib import Path

from ...errors import ProviderError
from .base import ProgressCallback, TranscriptionProvider, TranscriptionResult, TranscriptionSegment

#: Loaded models are cached across providers so switching screens does not
#: re-download a multi-hundred-megabyte checkpoint.
_MODEL_CACHE: dict[str, object] = {}

_INSTALL_HINT = "Install it with:  pip install openai-whisper"


class WhisperLocalProvider(TranscriptionProvider):
    """Runs Whisper locally on the CPU or GPU."""

    name = "whisper_local"
    label = "Whisper (local, offline)"
    requirements = "Needs the 'openai-whisper' package"

    def is_available(self) -> bool:
        return importlib.util.find_spec("whisper") is not None

    def _model_size(self) -> str:
        return getattr(self.settings, "whisper_model_size", "base") or "base"

    def _language(self) -> str | None:
        language = getattr(self.settings, "whisper_language", "auto") or "auto"
        return None if language in {"auto", "", None} else language

    def transcribe(
        self, audio_path: Path, progress: ProgressCallback | None = None
    ) -> TranscriptionResult:
        if not self.is_available():
            from ...errors import ProviderUnavailableError

            raise ProviderUnavailableError(
                "The 'openai-whisper' package is not installed.", _INSTALL_HINT
            )

        path = Path(audio_path)
        if not path.exists():
            raise ProviderError(f"Audio file not found: {path}")

        try:
            import whisper  # noqa: PLC0415 - optional dependency
        except ImportError as exc:  # pragma: no cover - guarded by is_available
            from ...errors import ProviderUnavailableError

            raise ProviderUnavailableError(
                "The 'openai-whisper' package is not installed.", _INSTALL_HINT
            ) from exc

        size = self._model_size()
        if progress:
            progress(f"Loading Whisper '{size}' model...")

        model = _MODEL_CACHE.get(size)
        if model is None:
            try:
                model = whisper.load_model(size)
            except Exception as exc:
                raise ProviderError(f"Could not load the Whisper model: {exc}") from exc
            _MODEL_CACHE[size] = model

        if progress:
            progress("Transcribing audio...")

        try:
            result = model.transcribe(
                str(path),
                fp16=False,
                language=self._language(),
                verbose=False,
            )
        except Exception as exc:
            raise ProviderError(f"Transcription failed: {exc}") from exc

        segments = [
            TranscriptionSegment(
                start=float(seg.get("start", 0.0)),
                end=float(seg.get("end", 0.0)),
                text=(seg.get("text") or "").strip(),
            )
            for seg in result.get("segments", []) or []
        ]

        return TranscriptionResult(
            text=(result.get("text") or "").strip(),
            segments=segments,
            provider=self.name,
            language=str(result.get("language") or ""),
        )
