"""Microphone capture.

``sounddevice`` is an optional dependency: when it is missing the recorder
raises :class:`ProviderUnavailableError` with an actionable hint instead of
crashing the application.
"""

from __future__ import annotations

import importlib.util
import wave
from pathlib import Path
from typing import Any

from ..errors import ProviderUnavailableError

_INSTALL_HINT = "Install it with:  pip install sounddevice numpy"


def _sounddevice():
    if importlib.util.find_spec("sounddevice") is None:
        raise ProviderUnavailableError(
            "The 'sounddevice' package is required to record audio.", _INSTALL_HINT
        )
    import sounddevice  # noqa: PLC0415 - optional dependency, imported lazily

    return sounddevice


def sounddevice_available() -> bool:
    """True when the optional audio dependency is importable."""
    try:
        _sounddevice()
    except ProviderUnavailableError:
        return False
    return True


def list_input_devices() -> list[dict[str, Any]]:
    """Available input devices, for the device picker."""
    try:
        sd = _sounddevice()
    except ProviderUnavailableError:
        return []

    devices = []
    try:
        raw = sd.query_devices()
    except Exception:  # pragma: no cover - depends on host audio stack
        return []
    for index, device in enumerate(raw):
        if device.get("max_input_channels", 0) > 0:
            devices.append(
                {
                    "index": index,
                    "name": device.get("name", f"Device {index}"),
                    "channels": device.get("max_input_channels", 1),
                    "default_samplerate": device.get("default_samplerate", 44100),
                }
            )
    return devices


def read_wave_duration(path: Path) -> float:
    """Duration of a WAV file in seconds."""
    try:
        with wave.open(str(path), "rb") as handle:
            frames = handle.getnframes()
            rate = handle.getframerate() or 1
            return frames / float(rate)
    except (OSError, wave.Error):
        return 0.0


class AudioRecorder:
    """Records mono audio from the microphone into a WAV file."""

    def __init__(self, samplerate: int = 44100, channels: int = 1, device: int | None = None):
        self.samplerate = samplerate
        self.channels = channels
        self.device = device
        self.recording = False
        self.level = 0.0  # peak level of the most recent block, 0.0 - 1.0
        self.elapsed = 0.0  # seconds recorded so far
        self._chunks: list[Any] = []
        self._stream = None
        self._frames = 0

    # ------------------------------------------------------------------ #
    def start(self) -> None:
        """Begin capturing audio."""
        if self.recording:
            return
        sd = _sounddevice()

        import numpy as np  # noqa: PLC0415 - optional dependency

        self._chunks = []
        self._frames = 0
        self.level = 0.0
        self.elapsed = 0.0

        def callback(indata, frames, time_info, status):  # noqa: ANN001, ARG001
            if status:
                print(f"[Audio] {status}")
            self._chunks.append(indata.copy())
            self._frames += frames
            peak = float(np.max(np.abs(indata))) if indata.size else 0.0
            self.level = min(1.0, peak)

        try:
            self._stream = sd.InputStream(
                callback=callback,
                channels=self.channels,
                samplerate=self.samplerate,
                device=self.device,
                dtype="float32",
            )
            self._stream.start()
        except Exception as exc:  # pragma: no cover - depends on host audio stack
            raise ProviderUnavailableError(
                f"Could not open the microphone: {exc}",
                "Check that a microphone is connected and not in use by another app.",
            ) from exc

        self.recording = True

    def stop(self, output_path: Path | None = None) -> Path | None:
        """Stop capturing and optionally write the WAV file.

        Returns the path of the written file, or ``None`` when nothing was
        captured or no destination was given.
        """
        if not self.recording:
            return None

        self.recording = False
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:  # pragma: no cover - stream may already be closed
                pass
            self._stream = None

        if not self._chunks:
            return None

        import numpy as np  # noqa: PLC0415 - optional dependency

        audio = np.concatenate(self._chunks, axis=0)
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        pcm = np.clip(audio, -1.0, 1.0)
        pcm = (pcm * 32767).astype(np.int16)

        if output_path is None:
            return None

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with wave.open(str(output_path), "wb") as handle:
            handle.setnchannels(1)
            handle.setsampwidth(2)
            handle.setframerate(self.samplerate)
            handle.writeframes(pcm.tobytes())

        self.elapsed = len(pcm) / float(self.samplerate)
        return output_path

    def cancel(self) -> None:
        """Discard the recording without writing a file."""
        self.stop(None)
        self._chunks = []

    # ------------------------------------------------------------------ #
    @property
    def duration(self) -> float:
        """Seconds of audio captured so far."""
        return self._frames / float(self.samplerate) if self.samplerate else 0.0
