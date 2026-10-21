"""Tests for the settings file."""

from __future__ import annotations

import json

from storytobook.settings import AppSettings


class TestDefaults:
    def test_uses_sensible_defaults(self):
        settings = AppSettings()
        assert settings.transcription_provider == "whisper_local"
        assert settings.cover_provider == "auto"
        assert settings.chapter_target_words == 1000
        assert settings.default_export_format == "pdf"


class TestPersistence:
    def test_save_and_load_round_trip(self, tmp_path):
        target = tmp_path / "settings.json"
        settings = AppSettings()
        settings.openai_api_key = "sk-test"
        settings.cover_steps = 12
        settings.save(target)

        loaded = AppSettings().load(target)
        assert loaded.openai_api_key == "sk-test"
        assert loaded.cover_steps == 12

    def test_missing_file_yields_defaults(self, tmp_path):
        loaded = AppSettings().load(tmp_path / "nope.json")
        assert loaded.transcription_provider == "whisper_local"

    def test_corrupt_file_yields_defaults(self, tmp_path):
        target = tmp_path / "settings.json"
        target.write_text("{ broken", encoding="utf-8")
        assert AppSettings().load(target).cover_steps == 30

    def test_unknown_keys_are_ignored(self, tmp_path):
        target = tmp_path / "settings.json"
        target.write_text(json.dumps({"cover_steps": 5, "bogus": 1}), encoding="utf-8")
        loaded = AppSettings().load(target)
        assert loaded.cover_steps == 5

    def test_save_leaves_no_temp_file(self, tmp_path):
        target = tmp_path / "settings.json"
        AppSettings().save(target)
        assert not list(tmp_path.glob("*.tmp"))


class TestValidation:
    def test_clamps_out_of_range_values(self):
        settings = AppSettings()
        settings.update(cover_steps=5000, cover_width=1, cover_guidance_scale=99.0)
        assert settings.cover_steps == 150
        assert settings.cover_width == 256
        assert settings.cover_guidance_scale == 20.0

    def test_rejects_unknown_appearance_mode(self):
        settings = AppSettings()
        settings.update(appearance_mode="rainbow")
        assert settings.appearance_mode == "dark"

    def test_rejects_unknown_export_format(self):
        settings = AppSettings()
        settings.update(default_export_format="docx")
        assert settings.default_export_format == "pdf"

    def test_chapter_length_has_a_floor(self):
        settings = AppSettings()
        settings.update(chapter_target_words=1)
        assert settings.chapter_target_words == 100
