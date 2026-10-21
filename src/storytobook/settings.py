"""User settings with JSON persistence."""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, fields
from pathlib import Path
from typing import Any

from . import paths


@dataclass
class AppSettings:
    """Everything the user can tune from the Settings screen."""

    # --- Transcription -----------------------------------------------------
    transcription_provider: str = "whisper_local"
    whisper_model_size: str = "base"
    whisper_language: str = "auto"
    openai_api_key: str = ""
    openai_transcription_model: str = "whisper-1"

    # --- Cover art ---------------------------------------------------------
    cover_provider: str = "auto"
    cover_base_model: str = "stable-diffusion-v1-5/stable-diffusion-v1-5"
    cover_lora_path: str = ""
    cover_use_lora: bool = False
    cover_steps: int = 30
    cover_guidance_scale: float = 7.5
    cover_width: int = 1200
    cover_height: int = 1600
    cover_seed: int = -1
    cover_extra_prompt: str = ""

    # --- Writing -----------------------------------------------------------
    chapter_target_words: int = 1000

    # --- Output ------------------------------------------------------------
    default_export_format: str = "pdf"

    # --- Interface ---------------------------------------------------------
    appearance_mode: str = "dark"
    accent_color: str = "blue"

    # ------------------------------------------------------------------ #
    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AppSettings:
        """Build settings from a mapping, ignoring unknown or malformed keys."""
        known = {f.name for f in fields(cls)}
        clean: dict[str, Any] = {}
        for key, value in (data or {}).items():
            if key not in known or value is None:
                continue
            clean[key] = value
        instance = cls(**clean)
        instance.sanitise()
        return instance

    def sanitise(self) -> None:
        """Clamp values into sane ranges so a hand-edited file cannot break the app."""
        self.whisper_model_size = self.whisper_model_size or "base"
        self.chapter_target_words = max(100, int(self.chapter_target_words or 1000))
        self.cover_steps = max(1, min(150, int(self.cover_steps or 30)))
        self.cover_guidance_scale = max(0.0, min(20.0, float(self.cover_guidance_scale or 7.5)))
        self.cover_width = max(256, min(2048, int(self.cover_width or 1200)))
        self.cover_height = max(256, min(2048, int(self.cover_height or 1600)))
        self.cover_seed = int(self.cover_seed)
        if self.appearance_mode not in {"dark", "light", "system"}:
            self.appearance_mode = "dark"
        if self.default_export_format not in {"pdf", "epub", "html"}:
            self.default_export_format = "pdf"

    def update(self, **kwargs: Any) -> None:
        """Apply a partial update and re-validate the result."""
        known = {f.name for f in fields(self)}
        for key, value in kwargs.items():
            if key in known and value is not None:
                setattr(self, key, value)
        self.sanitise()

    # ------------------------------------------------------------------ #
    def load(self, path: Path | None = None) -> AppSettings:
        """Read settings from disk. Missing or corrupt files yield defaults."""
        target = Path(path) if path else paths.settings_file()
        try:
            raw = target.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return self
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return self
        if isinstance(data, dict):
            self.update(**data)
        return self

    def save(self, path: Path | None = None) -> Path:
        """Persist settings atomically and return the file path."""
        target = Path(path) if path else paths.settings_file()
        target.parent.mkdir(parents=True, exist_ok=True)
        tmp = target.with_suffix(target.suffix + ".tmp")
        tmp.write_text(json.dumps(self.to_dict(), indent=2), encoding="utf-8")
        os.replace(tmp, target)
        return target
