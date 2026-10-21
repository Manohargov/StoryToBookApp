"""Exporter registry."""

from __future__ import annotations

from .base import BookExporter
from .epub import EpubExporter
from .html import HtmlExporter
from .pdf import PdfExporter

_REGISTRY: dict[str, type[BookExporter]] = {
    PdfExporter.name: PdfExporter,
    EpubExporter.name: EpubExporter,
    HtmlExporter.name: HtmlExporter,
}

#: Formats offered in the interface, in display order.
CHOICES: list[str] = ["pdf", "epub", "html"]


def list_exporters() -> list[BookExporter]:
    """Instantiate every known exporter."""
    return [_REGISTRY[name]() for name in CHOICES if name in _REGISTRY]


def build_exporter(name: str) -> BookExporter:
    """Return the exporter registered under ``name``."""
    exporter_cls = _REGISTRY.get(name) or PdfExporter
    return exporter_cls()
