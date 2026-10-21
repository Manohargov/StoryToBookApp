"""Single file HTML renderer.

The output is completely self-contained: the stylesheet is inlined and the
cover image is embedded as a base64 data URI, so the file can be shared or
opened offline as-is.
"""

from __future__ import annotations

import base64
import html
from pathlib import Path

from .base import BookDocument, BookExporter

_CSS = """
:root { color-scheme: light dark; }
* { box-sizing: border-box; }
body {
  margin: 0; padding: 0;
  font-family: Georgia, 'Iowan Old Style', 'Times New Roman', serif;
  line-height: 1.75; color: #222; background: #fbfaf7;
}
.book { max-width: 46rem; margin: 0 auto; padding: 3rem 1.5rem 5rem; }
.cover { text-align: center; margin: 0 0 3rem; }
.cover img { max-width: 100%; border-radius: 4px; box-shadow: 0 18px 40px rgba(0,0,0,.22); }
.title-page { text-align: center; padding: 3rem 0 4rem; border-bottom: 1px solid #e3ded4; }
.title-page h1 { font-size: 2.6rem; line-height: 1.15; margin: 0 0 1rem; }
.title-page .author { font-size: 1.15rem; letter-spacing: .12em; text-transform: uppercase; color: #5c564c; }
.title-page .publisher { margin-top: 2rem; font-style: italic; color: #7a746a; }
.front-matter h2, .chapter h2 { font-size: 1.5rem; margin: 2.5rem 0 1rem; }
.front-matter p, .chapter p { text-align: justify; margin: 0 0 1.1em; }
.toc { list-style: none; padding: 0; }
.toc li { padding: .45rem 0; border-bottom: 1px dotted #ddd7cb; }
.chapter { page-break-before: always; margin-top: 3rem; }
.colophon { text-align: center; margin-top: 4rem; padding-top: 2rem; border-top: 1px solid #e3ded4; color: #6b6559; font-style: italic; }
footer { text-align: center; padding: 2rem 0; color: #9a9387; font-size: .85rem; }
@media (prefers-color-scheme: dark) {
  body { background: #16171b; color: #e6e3dd; }
  .title-page { border-color: #2b2d33; }
  .title-page .author { color: #a9a396; }
  .toc li { border-color: #2b2d33; }
  .colophon { border-color: #2b2d33; color: #8d877c; }
}
"""


class HtmlExporter(BookExporter):
    """Renders a book as a single, portable HTML file."""

    name = "html"
    label = "HTML (single file)"
    extension = ".html"

    def export(self, document: BookDocument, output_dir: Path, filename_stem: str) -> Path:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{filename_stem}{self.extension}"

        cover_html = ""
        if document.cover_path and Path(document.cover_path).exists():
            encoded = self._embed_cover(Path(document.cover_path))
            if encoded:
                cover_html = f'<div class="cover"><img src="{encoded}" alt="Cover"/></div>'

        chapters_html = []
        for index, chapter in enumerate(document.chapters, start=1):
            title = html.escape(chapter.title.strip() or f"Chapter {index}")
            body = "\n".join(
                f"<p>{html.escape(paragraph)}</p>"
                for paragraph in self._paragraphs(chapter.text)
            )
            chapters_html.append(f'<section class="chapter"><h2>{title}</h2>{body}</section>')

        toc_items = "\n".join(
            f'<li>{html.escape(chapter.title.strip() or f"Chapter {index}")}</li>'
            for index, chapter in enumerate(document.chapters, start=1)
        )

        publisher = (
            f'<p class="publisher">{html.escape(document.publisher)}</p>'
            if document.publisher
            else ""
        )
        author = (
            f'<p class="author">{html.escape(document.author)}</p>'
            if document.author
            else ""
        )

        acknowledgment = "\n".join(
            f"<p>{html.escape(p)}</p>" for p in self._paragraphs(document.acknowledgment)
        ) or "<p>Thank you for reading.</p>"
        author_note = "\n".join(
            f"<p>{html.escape(p)}</p>" for p in self._paragraphs(document.author_note)
        ) or "<p>Written with StoryToBook.</p>"

        content = f"""<!DOCTYPE html>
<html lang="{html.escape(document.language)}">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>{html.escape(document.title)}</title>
<style>{_CSS}</style>
</head>
<body>
<main class="book">
{cover_html}
<header class="title-page">
  <h1>{html.escape(document.title)}</h1>
  {author}
  {publisher}
</header>
<section class="front-matter">
  <h2>Acknowledgment</h2>
  {acknowledgment}
  <h2>Author's Note</h2>
  {author_note}
</section>
<nav>
  <h2>Contents</h2>
  <ol class="toc">
{toc_items}
  </ol>
</nav>
{"".join(chapters_html)}
<section class="colophon">
  <p>Thank you for reading!</p>
  {f"<p>Written by {html.escape(document.author)}</p>" if document.author else ""}
  {f"<p>Published by {html.escape(document.publisher)}</p>" if document.publisher else ""}
  <p>All rights reserved.</p>
</section>
<footer>Created with StoryToBook</footer>
</main>
</body>
</html>
"""

        output_path.write_text(content, encoding="utf-8")
        return output_path

    # ------------------------------------------------------------------ #
    @staticmethod
    def _paragraphs(text: str) -> list[str]:
        return [p.strip() for p in (text or "").split("\n") if p.strip()]

    @staticmethod
    def _embed_cover(path: Path) -> str:
        try:
            data = path.read_bytes()
        except OSError:
            return ""
        mime = "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
        return f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}"
