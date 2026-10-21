"""Command line entry point: ``python -m storytobook``.

``storytobook --selftest`` runs the whole pipeline without opening a window.
It is used by the release workflow to prove that a frozen build really works.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path


def _selftest(report_path: Path | None = None) -> int:
    """Build a small book and report what happened.  Returns an exit code.

    A frozen build is a windowed application, so ``sys.stdout`` may not exist.
    The report is therefore also written to ``report_path`` when one is given.
    """
    from storytobook.domain.project import Project
    from storytobook.exporters.base import BookDocument
    from storytobook.exporters.registry import build_exporter
    from storytobook.providers.cover.base import CoverRequest
    from storytobook.providers.cover.pillow_fallback import PillowCoverProvider

    lines: list[str] = []
    steps: list[tuple[str, bool]] = []

    def report(line: str = "") -> None:
        lines.append(line)
        print(line)

    report("StoryToBook self test")
    report("-" * 40)

    try:
        from storytobook.domain.chapter import build_chapters, format_transcript

        text = (
            "Chapter 1 The Harbour. The ferry left at dawn and the sea was flat. "
            "Maren stood at the rail and watched the town disappear. "
            "Chapter 2 The Island. The island rose out of the water like a "
            "green shape nobody had asked for. Nobody came to meet them."
        )
        formatted = format_transcript(text)
        chapters = build_chapters(formatted, 200)
        steps.append(("chaptering", len(chapters) == 2))
        report(f"  chaptering    : {len(chapters)} chapters")
    except Exception as exc:
        steps.append(("chaptering", False))
        report(f"  chaptering    : FAILED ({exc})")

    cover_path: Path | None = None
    try:
        with tempfile.TemporaryDirectory() as tmp:
            cover_path = Path(tmp) / "cover.png"
            result = PillowCoverProvider().generate(
                CoverRequest(
                    story_text=text,
                    title="The Turning Tide",
                    author="Maren Vale",
                    output_path=cover_path,
                    width=400,
                    height=540,
                )
            )
            steps.append(("cover", cover_path.exists() and cover_path.stat().st_size > 1000))
            report(f"  cover art     : {result.genre}, {cover_path.stat().st_size} bytes")
    except Exception as exc:
        steps.append(("cover", False))
        report(f"  cover art     : FAILED ({exc})")

    for export_format in ("pdf", "epub", "html"):
        try:
            with tempfile.TemporaryDirectory() as tmp:
                project = Project(title="The Turning Tide", author="Maren Vale")
                project.chapters = chapters
                document = BookDocument.from_project(project, cover_path)
                exporter = build_exporter(export_format)
                path = exporter.export(document, Path(tmp), "The Turning Tide")
                ok = path.exists() and path.stat().st_size > 500
                steps.append((export_format, ok))
                report(f"  export {export_format:<5} : {path.stat().st_size} bytes")
        except Exception as exc:
            steps.append((export_format, False))
            report(f"  export {export_format:<5} : FAILED ({exc})")

    try:
        import customtkinter  # noqa: F401

        steps.append(("gui", True))
        report("  interface     : customtkinter available")
    except Exception as exc:
        steps.append(("gui", False))
        report(f"  interface     : FAILED ({exc})")

    report("-" * 40)
    failed = [name for name, ok in steps if not ok]
    if failed:
        report(f"FAILED: {', '.join(failed)}")
    else:
        report("All checks passed.")

    if report_path is not None:
        try:
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        except OSError:
            pass

    return 1 if failed else 0


def main() -> int:
    """Start the graphical application."""
    if "--selftest" in sys.argv:
        report: Path | None = None
        if "--report" in sys.argv:
            index = sys.argv.index("--report")
            if index + 1 < len(sys.argv):
                report = Path(sys.argv[index + 1])
        return _selftest(report)

    if "--version" in sys.argv:
        from .version import __version__

        print(__version__)
        return 0

    try:
        import customtkinter  # noqa: F401
    except ImportError:
        sys.stderr.write(
            "StoryToBook needs 'customtkinter'.\n"
            "Install the dependencies with:  pip install -r requirements.txt\n"
        )
        return 1

    from .app import main as run_app

    return run_app()


if __name__ == "__main__":
    raise SystemExit(main())
