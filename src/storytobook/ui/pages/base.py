"""Base class shared by every screen."""

from __future__ import annotations

import customtkinter as ctk

from ..theme import COLORS


class Page(ctk.CTkFrame):
    """A screen in the application.

    Pages are created once and shown with ``tkraise``.  Any work that has to
    happen when a page becomes visible belongs in :meth:`on_show`, never in
    ``__init__`` - that was the root cause of the processing starting at
    launch in the original application.
    """

    #: Title shown in the navigation bar.
    title = "Page"
    #: Whether the page appears in the sidebar.
    in_nav = True

    def __init__(self, master, app):
        super().__init__(master, fg_color="transparent")
        self.app = app
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

    # ------------------------------------------------------------------ #
    def on_show(self, **kwargs) -> None:
        """Called every time the page becomes visible."""

    def on_hide(self) -> None:
        """Called every time the page is navigated away from."""

    # ------------------------------------------------------------------ #
    def build(self) -> None:
        """Create the widgets.  Overridden by subclasses."""

    # ------------------------------------------------------------------ #
    @property
    def status_color(self) -> str:
        return COLORS["muted"]
