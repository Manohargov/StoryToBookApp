"""Cover art providers."""

from __future__ import annotations

from .base import CoverProvider, CoverRequest, CoverResult
from .diffusers_local import DiffusersCoverProvider
from .openai_api import OpenAICoverProvider
from .pillow_fallback import PillowCoverProvider

__all__ = [
    "CoverProvider",
    "CoverRequest",
    "CoverResult",
    "DiffusersCoverProvider",
    "OpenAICoverProvider",
    "PillowCoverProvider",
]

_REGISTRY: dict[str, type[CoverProvider]] = {
    DiffusersCoverProvider.name: DiffusersCoverProvider,
    OpenAICoverProvider.name: OpenAICoverProvider,
    PillowCoverProvider.name: PillowCoverProvider,
}

#: Providers offered in the interface, in preference order.
CHOICES: list[str] = ["auto", "diffusers_local", "openai_api", "pillow"]


def list_cover_providers() -> list[CoverProvider]:
    """Instantiate every known provider."""
    return [_REGISTRY[name]() for name in CHOICES if name in _REGISTRY]


def build_cover_provider(name: str, settings=None) -> CoverProvider:
    """Return the provider registered under ``name``.

    ``auto`` picks the best provider that is actually installed and falls
    back to the procedural Pillow cover, which always works offline.
    """
    if name in {"auto", "", None}:
        for candidate_name in ("diffusers_local", "openai_api"):
            candidate_cls = _REGISTRY.get(candidate_name)
            if candidate_cls is None:
                continue
            candidate = candidate_cls(settings)
            if candidate.is_available():
                return candidate
        return PillowCoverProvider(settings)

    provider_cls = _REGISTRY.get(name) or PillowCoverProvider
    provider = provider_cls(settings)
    if provider.is_available():
        return provider
    return PillowCoverProvider(settings)
