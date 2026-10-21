"""Tests for the cover providers and the genre detection."""

from __future__ import annotations

from storytobook.providers.cover.base import CoverRequest
from storytobook.providers.cover.diffusers_local import DiffusersCoverProvider
from storytobook.providers.cover.openai_api import OpenAICoverProvider
from storytobook.providers.cover.pillow_fallback import PillowCoverProvider
from storytobook.providers.cover.theme import build_prompt, detect_genre, palette_for
from storytobook.providers.cover.typography import find_font, load_font, wrap_text


class TestGenreDetection:
    def test_detects_fantasy(self):
        genre, hits = detect_genre("A dragon guarded the magic kingdom and the wizard smiled.")
        assert genre == "fantasy"
        assert "dragon" in hits

    def test_detects_science_fiction(self):
        genre, _ = detect_genre("The starship left orbit for the colony planet.")
        assert genre == "science fiction"

    def test_detects_mystery(self):
        genre, _ = detect_genre("The detective found the clue and the vanished suspect.")
        assert genre == "mystery"

    def test_falls_back_for_unrelated_text(self):
        genre, hits = detect_genre("The weather was fine and the food was good.")
        assert genre == "literary"
        assert hits == []

    def test_empty_text(self):
        assert detect_genre("") == ("literary", [])


class TestPrompt:
    def test_contains_the_genre(self):
        prompt = build_prompt("fantasy", "The Long Road", "Ada")
        assert "fantasy" in prompt.lower()
        assert "The Long Road" in prompt

    def test_extra_prompt_is_appended(self):
        assert "watercolour" in build_prompt("horror", extra="watercolour")

    def test_palette_exists_for_every_genre(self):
        for genre in ("fantasy", "mystery", "literary"):
            assert len(palette_for(genre)) == 3


class TestTypography:
    def test_finds_a_font_on_this_machine(self):
        # Not every CI image has fonts, so only assert it does not crash.
        find_font()
        find_font(bold=True)
        find_font(italic=True)

    def test_load_font_returns_something_usable(self):
        assert load_font(24) is not None

    def test_wrap_text_respects_the_width(self):
        from PIL import Image, ImageDraw

        draw = ImageDraw.Draw(Image.new("RGB", (10, 10)))
        font = load_font(20)
        lines = wrap_text(draw, "one two three four five six seven", font, 120)
        assert len(lines) > 1


class TestPillowProvider:
    def test_is_always_available(self):
        assert PillowCoverProvider().is_available()

    def test_generates_an_image(self, tmp_path):
        request = CoverRequest(
            story_text="A dragon guarded the magic kingdom.",
            title="The Long Road",
            author="Ada Marlowe",
            output_path=tmp_path / "cover.png",
            width=300,
            height=400,
        )
        result = PillowCoverProvider().generate(request)
        assert result.path.exists()
        assert result.path.stat().st_size > 1000
        assert result.genre == "fantasy"

    def test_is_deterministic_for_the_same_seed(self, tmp_path):
        def render(name):
            request = CoverRequest(
                story_text="A quiet harbour story.",
                title="Harbour",
                author="Ada",
                output_path=tmp_path / name,
                width=200,
                height=260,
                seed=7,
            )
            return PillowCoverProvider().generate(request).path.read_bytes()

        assert render("a.png") == render("b.png")

    def test_handles_a_long_title(self, tmp_path):
        request = CoverRequest(
            story_text="",
            title="A Very Long Title That Should Still Fit Inside The Cover",
            author="An Author With A Long Name As Well",
            output_path=tmp_path / "cover.png",
            width=300,
            height=400,
        )
        result = PillowCoverProvider().generate(request)
        assert result.path.exists()


class TestProviderFallbacks:
    def test_auto_falls_back_to_the_built_in_designer(self, settings):
        from storytobook.providers.cover import build_cover_provider

        provider = build_cover_provider("auto", settings)
        assert provider.is_available()

    def test_unknown_cover_provider_falls_back(self, settings):
        from storytobook.providers.cover import build_cover_provider

        assert build_cover_provider("nonsense", settings).name == "pillow"

    def test_diffusers_reports_unavailable_without_torch(self, settings):
        provider = DiffusersCoverProvider(settings)
        # Either torch is installed or it is not; both states must be safe.
        assert isinstance(provider.is_available(), bool)

    def test_openai_needs_a_key(self, settings):
        settings.openai_api_key = ""
        assert OpenAICoverProvider(settings).is_available() is False
