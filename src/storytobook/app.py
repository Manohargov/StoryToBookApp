"""The application shell: navigation, page routing and background work."""

from __future__ import annotations

import queue
import threading
import traceback
from collections.abc import Callable
from typing import Any

import customtkinter as ctk

from . import paths
from .errors import StoryToBookError
from .services.library import Library
from .services.pipeline import BookPipeline, Progress
from .settings import AppSettings
from .ui.pages.base import Page
from .ui.theme import COLORS, SIZES, hero_font, muted_font
from .version import __version__

#: Navigation entries: page class name and its label.
NAV_ITEMS: list[tuple[str, str]] = [
    ("LandingPage", "Home"),
    ("DashboardPage", "Library"),
    ("RecordingPage", "Record"),
    ("TranscriptPage", "Story"),
    ("DetailsPage", "Details"),
    ("ExportPage", "Export"),
    ("SettingsPage", "Settings"),
]


class StoryApp(ctk.CTk):
    """Main window."""

    def __init__(self) -> None:
        super().__init__()

        self.title(f"Story to Book  ·  {__version__}")
        self.geometry("1180x760")
        self.minsize(1000, 640)

        self.settings = AppSettings().load()
        self.library = Library()
        self.pipeline = BookPipeline(self.library, self.settings)
        self.project = None

        self._pages: dict[str, Page] = {}
        self._nav_buttons: dict[str, ctk.CTkButton] = {}
        self._queue: queue.Queue = queue.Queue()
        self._current: str | None = None
        self._closing = False

        self._build_layout()
        self._build_pages()
        self._start_pump()

        self.navigate("LandingPage")
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------ #
    # Layout
    # ------------------------------------------------------------------ #
    def _build_layout(self) -> None:
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        sidebar = ctk.CTkFrame(self, width=210, corner_radius=0, fg_color=COLORS["surface"])
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_rowconfigure(1, weight=1)
        sidebar.grid_columnconfigure(0, weight=1)

        brand = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand.grid(row=0, column=0, sticky="ew", padx=18, pady=(22, 10))
        ctk.CTkLabel(
            brand, text="Story to Book", font=hero_font(20), anchor="w"
        ).pack(anchor="w")
        ctk.CTkLabel(
            brand,
            text="Turn your voice into a book",
            font=muted_font(SIZES["tiny"]),
            text_color=COLORS["muted"],
            anchor="w",
        ).pack(anchor="w", pady=(2, 0))

        nav = ctk.CTkFrame(sidebar, fg_color="transparent")
        nav.grid(row=1, column=0, sticky="new", padx=12)
        for index, (page_name, label) in enumerate(NAV_ITEMS):
            button = ctk.CTkButton(
                nav,
                text=label,
                anchor="w",
                height=38,
                corner_radius=9,
                fg_color="transparent",
                text_color=COLORS["muted"],
                hover_color=COLORS["surface_alt"],
                command=lambda name=page_name: self.navigate(name),
            )
            button.grid(row=index, column=0, sticky="ew", pady=2)
            self._nav_buttons[page_name] = button

        footer = ctk.CTkFrame(sidebar, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", padx=18, pady=(8, 18))
        self.data_path_label = ctk.CTkLabel(
            footer,
            text=str(paths.data_dir()),
            font=muted_font(10),
            text_color=COLORS["muted"],
            anchor="w",
            justify="left",
            wraplength=170,
        )
        self.data_path_label.pack(anchor="w")
        ctk.CTkButton(
            footer,
            text="Open data folder",
            height=28,
            corner_radius=8,
            fg_color="transparent",
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["muted"],
            hover_color=COLORS["surface_alt"],
            command=self.open_data_folder,
        ).pack(anchor="w", fill="x", pady=(8, 0))

        content = ctk.CTkFrame(self, fg_color="transparent")
        content.grid(row=0, column=1, sticky="nsew")
        content.grid_rowconfigure(0, weight=1)
        content.grid_columnconfigure(0, weight=1)
        self.content = content

        status_bar = ctk.CTkFrame(self, height=32, corner_radius=0, fg_color=COLORS["surface"])
        status_bar.grid(row=1, column=0, columnspan=2, sticky="ew")
        status_bar.grid_columnconfigure(0, weight=1)
        self.status_label = ctk.CTkLabel(
            status_bar,
            text="Ready",
            font=muted_font(SIZES["small"]),
            text_color=COLORS["muted"],
            anchor="w",
        )
        self.status_label.grid(row=0, column=0, sticky="ew", padx=18, pady=4)
        self.busy_label = ctk.CTkLabel(
            status_bar,
            text="",
            font=muted_font(SIZES["small"]),
            text_color=COLORS["accent"],
            anchor="e",
        )
        self.busy_label.grid(row=0, column=1, sticky="e", padx=18, pady=4)

    def _build_pages(self) -> None:
        from .ui.pages.dashboard import DashboardPage
        from .ui.pages.details import DetailsPage
        from .ui.pages.export import ExportPage
        from .ui.pages.landing import LandingPage
        from .ui.pages.recording import RecordingPage
        from .ui.pages.settings import SettingsPage
        from .ui.pages.transcript import TranscriptPage

        classes = {
            "LandingPage": LandingPage,
            "DashboardPage": DashboardPage,
            "RecordingPage": RecordingPage,
            "TranscriptPage": TranscriptPage,
            "DetailsPage": DetailsPage,
            "ExportPage": ExportPage,
            "SettingsPage": SettingsPage,
        }
        for name, _ in NAV_ITEMS:
            page = classes[name](self.content, self)
            page.grid(row=0, column=0, sticky="nsew")
            self._pages[name] = page

    # ------------------------------------------------------------------ #
    # Navigation
    # ------------------------------------------------------------------ #
    def navigate(self, name: str, **kwargs) -> None:
        """Show a page and notify the previous one that it was left."""
        page = self._pages.get(name)
        if page is None:
            return

        if self._current and self._current != name:
            previous = self._pages.get(self._current)
            if previous is not None:
                previous.on_hide()

        for key, button in self._nav_buttons.items():
            active = key == name
            button.configure(
                fg_color=COLORS["accent"] if active else "transparent",
                text_color="#ffffff" if active else COLORS["muted"],
            )

        page.tkraise()
        self._current = name
        page.on_show(**kwargs)

    # ------------------------------------------------------------------ #
    # Background work
    # ------------------------------------------------------------------ #
    def _start_pump(self) -> None:
        self.after(80, self._pump)

    def _pump(self) -> None:
        if self._closing:
            return
        while True:
            try:
                kind, payload = self._queue.get_nowait()
            except queue.Empty:
                break
            try:
                if kind == "progress":
                    self._handle_progress(payload)
                elif kind == "callback":
                    callback, value = payload
                    callback(value)
                elif kind == "done":
                    result, callback = payload
                    if callback:
                        callback(result)
                elif kind == "error":
                    error, callback = payload
                    self._handle_error(error, callback)
            except Exception:
                traceback.print_exc()
        self.after(80, self._pump)

    def _handle_progress(self, progress: Progress) -> None:
        self.set_status(progress.message or "")
        self.busy_label.configure(text=progress.detail or progress.message or "")

    def _handle_error(self, error: Exception, callback: Callable | None) -> None:
        self.busy_label.configure(text="")
        message = str(error) or error.__class__.__name__
        self.set_status(f"Error: {message}")
        hint = getattr(error, "hint", "")
        if hint:
            self.set_status(f"{message} — {hint}")
        if callback:
            callback(error)
        else:
            self._show_error("Something went wrong", message, hint)

    def run_background(
        self,
        target: Callable[[Callable[[Progress], None]], Any],
        on_done: Callable[[Any], None] | None = None,
        on_error: Callable[[Exception], None] | None = None,
        on_progress: Callable[[Progress], None] | None = None,
        status: str = "Working...",
    ) -> None:
        """Run ``target`` on a worker thread and deliver the result safely.

        ``on_done``, ``on_error`` and ``on_progress`` are always invoked on
        the interface thread, so they may touch widgets freely.
        """

        def emit(progress: Progress) -> None:
            self._queue.put(("progress", progress))
            if on_progress:
                self._queue.put(("callback", (on_progress, progress)))

        def worker() -> None:
            try:
                result = target(emit)
                self._queue.put(("done", (result, on_done)))
            except Exception as exc:  # noqa: BLE001 - reported to the user
                self._queue.put(("error", (exc, on_error)))

        self.set_status(status)
        threading.Thread(target=worker, daemon=True).start()

    # ------------------------------------------------------------------ #
    # Helpers for pages
    # ------------------------------------------------------------------ #
    def set_status(self, text: str) -> None:
        self.status_label.configure(text=text)

    def clear_busy(self) -> None:
        self.busy_label.configure(text="")

    def _show_error(self, title: str, message: str, hint: str = "") -> None:
        from tkinter import messagebox

        text = message if not hint else f"{message}\n\n{hint}"
        messagebox.showerror(title, text)

    def open_data_folder(self) -> None:
        from .ui.system import open_path

        open_path(paths.data_dir())

    def require_project(self) -> bool:
        """Make sure a project is selected before continuing."""
        if self.project is None:
            self.set_status("Open a project from the library first.")
            self.navigate("DashboardPage")
            return False
        return True

    def new_project(self, title: str = "Untitled Story"):
        """Create a project, make it current and return it."""
        self.project = self.library.create(title=title)
        self.set_status(f"Created '{self.project.display_name}'.")
        return self.project

    def open_project(self, project_id: str) -> None:
        try:
            self.project = self.library.load(project_id)
        except StoryToBookError:
            self.set_status("That project could not be opened.")
            return
        self.set_status(f"Opened '{self.project.display_name}'.")

    def save_project(self) -> None:
        if self.project is not None:
            self.library.save(self.project)

    # ------------------------------------------------------------------ #
    def _on_close(self) -> None:
        self._closing = True
        try:
            self.save_project()
            self.settings.save()
        finally:
            self.destroy()


def main() -> int:
    """Entry point used by ``python -m storytobook``."""
    from .ui.theme import apply_theme

    paths.ensure_data_dirs()
    settings = AppSettings().load()
    apply_theme(settings.appearance_mode, settings.accent_color)

    app = StoryApp()
    app.mainloop()
    return 0
