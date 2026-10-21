"""EPUB 3 renderer built on the standard library.

Produces a valid, readable EPUB with a cover image, a navigation document and
one XHTML document per chapter.
"""

from __future__ import annotations

import uuid
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from .base import BookDocument, BookExporter

_CONTAINER_XML = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/package.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>
"""

_STYLE_CSS = """@page { margin: 5%; }
body { font-family: Georgia, 'Times New Roman', serif; line-height: 1.6; margin: 0 5%; }
h1 { font-size: 1.6em; margin: 1.2em 0 0.8em 0; text-align: center; }
h2 { font-size: 1.1em; margin: 1.6em 0 0.4em 0; }
p { margin: 0 0 0.9em 0; text-align: justify; }
.cover { text-align: center; }
.cover img { max-width: 100%; max-height: 100%; }
.meta { text-align: center; color: #444; font-style: italic; }
"""

_XHTML_TEMPLATE = """<?xml version="1.0" encoding="utf-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="{lang}" lang="{lang}">
<head>
  <meta charset="utf-8"/>
  <title>{title}</title>
  <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
{body}
</body>
</html>
"""


class EpubExporter(BookExporter):
    """Packages a book as an EPUB file."""

    name = "epub"
    label = "EPUB (e-readers)"
    extension = ".epub"

    def export(self, document: BookDocument, output_dir: Path, filename_stem: str) -> Path:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{filename_stem}{self.extension}"

        book_id = uuid.uuid5(uuid.NAMESPACE_URL, f"urn:storytobook:{document.title}")
        chapters = document.chapters or []

        manifest: list[str] = []
        spine: list[str] = []
        nav_items: list[tuple[str, str]] = []

        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as archive:
            # The mimetype entry must be first and stored uncompressed.
            archive.writestr(
                zipfile.ZipInfo("mimetype"),
                "application/epub+zip",
                compress_type=zipfile.ZIP_STORED,
            )
            archive.writestr("META-INF/container.xml", _CONTAINER_XML)
            archive.writestr("OEBPS/style.css", _STYLE_CSS)

            if document.cover_path and Path(document.cover_path).exists():
                archive.write(str(document.cover_path), "OEBPS/cover.png")
                manifest.append('<item id="cover-image" href="cover.png" media-type="image/png" properties="cover-image"/>')

            archive.writestr(
                "OEBPS/text/title.xhtml",
                _XHTML_TEMPLATE.format(
                    lang=document.language,
                    title=escape(document.title),
                    body=self._title_body(document),
                ),
            )
            manifest.append('<item id="title" href="text/title.xhtml" media-type="application/xhtml+xml"/>')
            spine.append("title")
            nav_items.append(("title", document.title))

            for index, chapter in enumerate(chapters, start=1):
                name = f"chapter_{index}.xhtml"
                title = chapter.title.strip() or f"Chapter {index}"
                archive.writestr(
                    f"OEBPS/text/{name}",
                    _XHTML_TEMPLATE.format(
                        lang=document.language,
                        title=escape(title),
                        body=self._chapter_body(title, chapter.text),
                    ),
                )
                manifest.append(
                    f'<item id="ch{index}" href="text/{name}" media-type="application/xhtml+xml"/>'
                )
                spine.append(f"ch{index}")
                nav_items.append((f"ch{index}", title))

            archive.writestr("OEBPS/nav.xhtml", self._nav_body(document, nav_items))
            manifest.append('<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>')

            archive.writestr("OEBPS/package.opf", self._package_opf(document, manifest, spine, book_id))
            archive.writestr("OEBPS/toc.ncx", self._toc_ncx(document, nav_items, book_id))

        return output_path

    # ------------------------------------------------------------------ #
    @staticmethod
    def _title_body(document: BookDocument) -> str:
        parts = ['<section class="cover">']
        if document.cover_path and Path(document.cover_path).exists():
            parts.append('<p><img src="../cover.png" alt="Cover"/></p>')
        parts.append(f"<h1>{escape(document.title)}</h1>")
        if document.author:
            parts.append(f'<p class="meta">{escape(document.author)}</p>')
        if document.publisher:
            parts.append(f'<p class="meta">{escape(document.publisher)}</p>')
        parts.append("</section>")
        return "\n".join(parts)

    @staticmethod
    def _chapter_body(title: str, text: str) -> str:
        parts = [f"<h1>{escape(title)}</h1>"]
        paragraphs = [p.strip() for p in (text or "").split("\n") if p.strip()]
        if not paragraphs:
            paragraphs = [""]
        for paragraph in paragraphs:
            parts.append(f"<p>{escape(paragraph)}</p>")
        return "\n".join(parts)

    @staticmethod
    def _nav_body(document: BookDocument, nav_items: list[tuple[str, str]]) -> str:
        entries = "\n".join(
            f'<li><a href="text/{item_id}.xhtml">{escape(label)}</a></li>'
            for item_id, label in nav_items
        )
        return _XHTML_TEMPLATE.format(
            lang=document.language,
            title=f"{document.title} - Contents",
            body=(
                '<nav epub:type="toc" id="toc">\n'
                "<h1>Contents</h1>\n"
                f"<ol>\n{entries}\n</ol>\n"
                "</nav>"
            ),
        )

    @staticmethod
    def _package_opf(document, manifest, spine, book_id) -> str:
        items = "\n".join(manifest)
        spine_items = "\n".join(f'<itemref idref="{ref}"/>' for ref in spine)
        publisher = escape(document.publisher) if document.publisher else "StoryToBook"
        return f"""<?xml version="1.0" encoding="utf-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid" xml:lang="{document.language}">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="bookid">urn:uuid:{book_id}</dc:identifier>
    <dc:title>{escape(document.title)}</dc:title>
    <dc:language>{document.language}</dc:language>
    <dc:publisher>{publisher}</dc:publisher>
    {f"<dc:creator>{escape(document.author)}</dc:creator>" if document.author else ""}
    <meta property="dcterms:modified">2024-01-01T00:00:00Z</meta>
  </metadata>
  <manifest>
    <item id="css" href="style.css" media-type="text/css"/>
{items}
  </manifest>
  <spine toc="ncx">
{spine_items}
  </spine>
</package>
"""

    @staticmethod
    def _toc_ncx(document, nav_items, book_id) -> str:
        points = []
        order = 0
        for item_id, label in nav_items:
            order += 1
            points.append(
                f"""    <navPoint id="np{order}" playOrder="{order}">
      <navLabel><text>{escape(label)}</text></navLabel>
      <content src="text/{item_id}.xhtml"/>
    </navPoint>"""
            )
        points_xml = "\n".join(points)
        return f"""<?xml version="1.0" encoding="utf-8"?>
<ncx xmlns="http://www.daisy.org/z3986/2005/ncx/" version="2005-1">
  <head>
    <meta name="dtb:uid" content="urn:uuid:{book_id}"/>
    <meta name="dtb:depth" content="1"/>
    <meta name="dtb:totalPageCount" content="0"/>
    <meta name="dtb:maxPageNumber" content="0"/>
  </head>
  <docTitle><text>{escape(document.title)}</text></docTitle>
  <navMap>
{points_xml}
  </navMap>
</ncx>
"""
