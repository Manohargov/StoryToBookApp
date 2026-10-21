"""Capture screenshots of the application with a seeded sample project.

Usage:  python scripts/screenshot_seeded.py <output-dir>
"""

from __future__ import annotations

import os
import sys
import tempfile

os.environ.setdefault("STORYTOBOOK_HOME", tempfile.mkdtemp(prefix="stb-seed-"))
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_ROOT, "src"))

from PIL import ImageGrab  # noqa: E402

from storytobook.app import StoryApp  # noqa: E402
from storytobook.domain.chapter import format_transcript  # noqa: E402
from storytobook.providers.cover.base import CoverRequest  # noqa: E402
from storytobook.providers.cover.pillow_fallback import PillowCoverProvider  # noqa: E402
from storytobook.ui.theme import apply_theme  # noqa: E402

STORY = (
    "Chapter 1 The Crossing. The ferry left the harbour at dawn and the sea was "
    "flat as a sheet of tin. Maren stood at the rail and watched the town "
    "shrink into the mist behind her. She had told herself she would not look "
    "back, and yet she looked, and the town was already gone. The wind carried "
    "the smell of salt and diesel and something sweeter that she could not name. "
    "On the deck behind her, her brother argued with a man about the weather. "
    "The argument was the same argument they had been having for nine years, "
    "and Maren let it wash over her like the sea. "
    "Chapter 2 The Island. The island appeared an hour before noon, a low green "
    "shape that seemed to rise out of the water rather than rest on it. Nobody "
    "came to meet them. The harbour was a single wooden pier, bleached nearly "
    "white by the sun, and a woman in a red coat who watched them land without "
    "moving at all. Maren stepped onto the pier and felt the ground shift, "
    "impossibly, beneath her feet. Her brother said nothing. The woman in the "
    "red coat turned and walked up the hill without waiting for them, and "
    "everyone, somehow, followed. "
    "Chapter 3 The House. The house was built of stone that had gone grey with "
    "weather, and it had more windows than Maren could count. Inside, the air "
    "smelled of dust and old smoke. A lamp burned on a table though no one had "
    "lit it. Her brother went deeper into the house, as he always did, and "
    "Maren stood in the doorway and listened to the silence settle around her "
    "like water. Somewhere far off, a door closed. She had the strong sense "
    "that the island had been waiting for them for a very long time, and that "
    "it had not been waiting for her brother at all. "
    "Chapter 4 The Names. They found the books in the cellar, row upon row of "
    "them, their spines faded to a soft grey. Every book was the same book. "
    "Maren opened one at random and found her own handwriting on the first "
    "page, and her own name at the top of it, and the date, and the date was "
    "tomorrow. She closed it. She opened another. The same handwriting, the "
    "same name, a different date, each one a little later than the last, and "
    "the last one was a long way from now. When she looked up, her brother "
    "was standing in the doorway with a book in his hands, reading it with an "
    "expression she had never seen on him before. "
    "Chapter 5 The Turning. The storm came in the night. It came from the sea "
    "and it did not stop, and in the morning the harbour was gone and the pier "
    "was gone and the road up the hill had turned into a river. Maren stood at "
    "the window of the house and watched the water climb the steps, one after "
    "another, like a slow patient hand. The woman in the red coat came in "
    "without knocking. She said the island had always belonged to the sea, and "
    "that the books had been left there so that someone would come to read "
    "them before it was too late. Maren thought of her brother, and of the "
    "date at the top of the page, and of how many times she had chosen to come "
    "back. The storm reached the door. The woman in the red coat took her "
    "hand. "
)


def seed(app: StoryApp) -> None:
    project = app.library.create(title="The Turning Tide")
    project.author = "Maren Vale"
    project.publisher = "Harbourlight Books"
    project.acknowledgment = (
        "For everyone who has ever waited at a harbour for someone who was "
        "not coming back, and for the readers of my first book."
    )
    project.author_note = (
        "This story was spoken aloud in a single afternoon and then typed out "
        "by hand. Thank you for listening to it."
    )
    project.transcript = format_transcript(STORY)

    from storytobook.domain.chapter import build_chapters

    project.chapters = build_chapters(STORY, 120)
    project.cover_filename = "cover.png"

    cover_path = app.library.cover_path(project.id)
    PillowCoverProvider().generate(
        CoverRequest(
            story_text=STORY,
            title=project.title,
            author=project.author,
            output_path=cover_path,
            width=900,
            height=1200,
        )
    )
    app.library.save(project)
    app.project = project


def main() -> int:
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    os.makedirs(out_dir, exist_ok=True)

    apply_theme("dark", "blue")
    app = StoryApp()
    app.geometry("1180x760+40+40")
    app.update_idletasks()
    app.update()
    seed(app)
    app.update_idletasks()
    app.update()

    pages = [
        ("LandingPage", "home"),
        ("DashboardPage", "dashboard"),
        ("RecordingPage", "record"),
        ("TranscriptPage", "story"),
        ("DetailsPage", "details"),
        ("ExportPage", "export"),
        ("SettingsPage", "settings"),
    ]

    def capture(index: int) -> None:
        if index >= len(pages):
            app.destroy()
            return
        page, slug = pages[index]
        app.navigate(page)
        app.update_idletasks()
        app.update()
        app.after(
            700,
            lambda: _shot(app, os.path.join(out_dir, f"{slug}.png"), index),
        )

    def _shot(app, path, index):
        app.update_idletasks()
        app.update()
        app.lift()
        app.attributes("-topmost", True)
        app.update_idletasks()
        app.update()

        shot = ImageGrab.grab()
        left = app.winfo_rootx()
        top = app.winfo_rooty()
        right = left + app.winfo_width()
        bottom = top + app.winfo_height()
        shot.crop((left, top, right, bottom)).save(path)
        app.attributes("-topmost", False)
        print(f"saved {path}")
        capture(index + 1)

    app.after(900, lambda: capture(0))
    app.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
