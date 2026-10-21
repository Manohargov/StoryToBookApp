"""Cover art from the OpenAI image API."""

from __future__ import annotations

import base64
import importlib.util
from pathlib import Path

from ...errors import ProviderError, ProviderUnavailableError
from .base import CoverProvider, CoverRequest, CoverResult
from .pillow_fallback import apply_title_overlay
from .theme import build_prompt, detect_genre

_INSTALL_HINT = "Install it with:  pip install openai  (and set an API key)"


class OpenAICoverProvider(CoverProvider):
    """Generates artwork with OpenAI's image models."""

    name = "openai_api"
    label = "OpenAI Images (cloud)"
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

    def generate(self, request: CoverRequest, progress=None) -> CoverResult:
        client = self._get_client()
        genre, _ = detect_genre(request.story_text)
        prompt = build_prompt(genre, request.title, request.author, request.extra_prompt)
        prompt += ". No text, no lettering, no watermark."

        if progress:
            progress("Requesting artwork from OpenAI...")

        size = "1024x1536"
        try:
            response = client.images.generate(
                model="gpt-image-1",
                prompt=prompt,
                size=size,
                n=1,
            )
        except Exception as exc:
            raise ProviderError(f"OpenAI image generation failed: {exc}") from exc

        data = getattr(response, "data", None)
        if not data:
            raise ProviderError("OpenAI returned no image data.")

        item = data[0]
        b64 = getattr(item, "b64_json", None)
        url = getattr(item, "url", None)

        import io  # noqa: PLC0415

        from PIL import Image  # noqa: PLC0415 - keeps the import local and cheap

        if b64:
            image = Image.open(io.BytesIO(base64.b64decode(b64)))
        elif url:
            import urllib.request  # noqa: PLC0415

            with urllib.request.urlopen(url) as handle:  # noqa: S310 - fixed API host
                image = Image.open(io.BytesIO(handle.read()))
        else:
            raise ProviderError("OpenAI returned an image without data.")

        image = image.convert("RGB").resize((request.width, request.height), Image.LANCZOS)
        image = apply_title_overlay(image, request.title, request.author)

        output_path = Path(request.output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path, "PNG", dpi=(300, 300))

        return CoverResult(
            path=output_path,
            provider=self.name,
            prompt=prompt,
            genre=genre,
        )
