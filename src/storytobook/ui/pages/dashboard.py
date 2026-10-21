"""The project library."""

from __future__ import annotations

from datetime import datetime

import customtkinter as ctk

from ..theme import COLORS, SIZES, Badge, Card, SectionTitle, StatTile, font, muted_font
from .base import Page


def _friendly_date(value: str) -> str:
    try:
        stamp = datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return ""
    delta = datetime.now(stamp.tzinfo) - stamp
    seconds = delta.total_seconds()
    if seconds < 60:
        return "just now"
    if seconds < 3600:
        return f"{int(seconds // 60)} min ago"
    if seconds < 86400:
        return f"{int(seconds // 3600)} h ago"
    if seconds < 604800:
        return f"{int(seconds // 86400)} d ago"
    return stamp.strftime("%d %b %Y")


class DashboardPage(Page):
    """Lists every project and offers the main actions."""

    title = "Library"

    def __init__(self, master, app):
        super().__init__(master, app)
        self._search = ""
        self.build()

    def build(self) -> None:
        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.grid(row=0, column=0, sticky="nsew")
        wrapper.grid_columnconfigure(0, weight=1)
        wrapper.grid_rowconfigure(2, weight=1)

        header = ctk.CTkFrame(wrapper, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=34, pady=(30, 0))
        header.grid_columnconfigure(0, weight=1)

        SectionTitle(
            header,
            "Your library",
            "Every book you are writing, ready to pick up where you left off.",
        ).grid(row=0, column=0, sticky="ew")

        stats = ctk.CTkFrame(header, fg_color="transparent")
        stats.grid(row=1, column=0, sticky="w", pady=(16, 0))
        self.stat_projects = StatTile(stats, "projects")
        self.stat_projects.grid(row=0, column=0, sticky="w", padx=(0, 34))
        self.stat_chapters = StatTile(stats, "chapters")
        self.stat_chapters.grid(row=0, column=1, sticky="w", padx=(0, 34))
        self.stat_words = StatTile(stats, "words")
        self.stat_words.grid(row=0, column=2, sticky="w")

        toolbar = ctk.CTkFrame(wrapper, fg_color="transparent")
        toolbar.grid(row=1, column=0, sticky="ew", padx=34, pady=(18, 10))
        toolbar.grid_columnconfigure(1, weight=1)

        self.search_entry = ctk.CTkEntry(
            toolbar,
            placeholder_text="Search by title or author...",
            width=260,
            height=38,
            corner_radius=9,
        )
        self.search_entry.grid(row=0, column=0, sticky="w")
        self.search_entry.bind("<KeyRelease>", lambda _e: self._refresh())

        ctk.CTkButton(
            toolbar,
            text="+  New project",
            width=150,
            height=38,
            corner_radius=9,
            font=font(SIZES["body"], "bold"),
            command=self._new_project,
        ).grid(row=0, column=2, sticky="e")

        self.list_frame = ctk.CTkScrollableFrame(wrapper, fg_color="transparent")
        self.list_frame.grid(row=2, column=0, sticky="nsew", padx=26, pady=(0, 26))
        self.list_frame.grid_columnconfigure(0, weight=1)

    # ------------------------------------------------------------------ #
    def on_show(self, **kwargs) -> None:
        self._refresh()

    def _refresh(self) -> None:
        query = self.search_entry.get().strip().lower() if self.winfo_exists() else ""
        self._search = query

        projects = self.app.library.list()
        usage = self.app.library.usage()
        self.stat_projects.set_value(usage["projects"])
        self.stat_chapters.set_value(usage["chapters"])
        self.stat_words.set_value(f"{usage['words']:,}")

        for child in self.list_frame.winfo_children():
            child.destroy()

        if query:
            projects = [
                p
                for p in projects
                if query in p.display_name.lower() or query in (p.author or "").lower()
            ]

        if not projects:
            self._show_empty(query)
            return

        for index, project in enumerate(projects):
            self._add_card(index, project)

    def _show_empty(self, query: str) -> None:
        empty = Card(self.list_frame)
        empty.grid(row=0, column=0, sticky="ew", padx=8, pady=12)
        empty.grid_columnconfigure(0, weight=1)

        if query:
            message = f'Nothing matches "{query}".'
            hint = "Try a different search term."
        else:
            message = "Your library is empty."
            hint = "Start a new project to record your first story."

        ctk.CTkLabel(
            empty, text=message, font=font(SIZES["subtitle"], "bold"), anchor="w"
        ).grid(row=0, column=0, sticky="ew", padx=24, pady=(26, 4))
        ctk.CTkLabel(
            empty,
            text=hint,
            font=muted_font(SIZES["body"]),
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=1, column=0, sticky="ew", padx=24, pady=(0, 22))
        ctk.CTkButton(
            empty,
            text="Start a new project",
            width=180,
            height=38,
            corner_radius=9,
            command=self._new_project,
        ).grid(row=2, column=0, sticky="w", padx=24, pady=(0, 26))

    def _add_card(self, index: int, project) -> None:
        card = Card(self.list_frame)
        card.grid(row=index, column=0, sticky="ew", padx=8, pady=6)
        card.grid_columnconfigure(1, weight=1)

        badge = Badge(card, project.status.label)
        badge.grid(row=0, column=0, rowspan=2, sticky="w", padx=(20, 16))

        ctk.CTkLabel(
            card,
            text=project.display_name,
            font=font(SIZES["subtitle"], "bold"),
            anchor="w",
        ).grid(row=0, column=1, sticky="ew", pady=(16, 0))

        details = []
        if project.author:
            details.append(project.author)
        details.append(f"{project.word_count:,} words")
        details.append(f"{project.chapter_count} chapters")
        details.append(_friendly_date(project.updated_at))

        ctk.CTkLabel(
            card,
            text="  ·  ".join(details),
            font=muted_font(SIZES["small"]),
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=1, column=1, sticky="ew", pady=(2, 14))

        actions = ctk.CTkFrame(card, fg_color="transparent")
        actions.grid(row=0, column=2, rowspan=2, sticky="e", padx=20)

        ctk.CTkButton(
            actions,
            text="Open",
            width=80,
            height=32,
            corner_radius=8,
            command=lambda pid=project.id: self._open(pid),
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            actions,
            text="Export",
            width=80,
            height=32,
            corner_radius=8,
            fg_color="transparent",
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            hover_color=COLORS["surface_alt"],
            command=lambda pid=project.id: self._export(pid),
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            actions,
            text="Duplicate",
            width=92,
            height=32,
            corner_radius=8,
            fg_color="transparent",
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["muted"],
            hover_color=COLORS["surface_alt"],
            command=lambda pid=project.id: self._duplicate(pid),
        ).pack(side="left", padx=(0, 6))
        ctk.CTkButton(
            actions,
            text="Delete",
            width=78,
            height=32,
            corner_radius=8,
            fg_color="transparent",
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["danger"],
            hover_color=COLORS["surface_alt"],
            command=lambda pid=project.id: self._delete(pid),
        ).pack(side="left")

    # ------------------------------------------------------------------ #
    def _new_project(self) -> None:
        self.app.new_project()
        self.app.navigate("RecordingPage")

    def _open(self, project_id: str) -> None:
        self.app.open_project(project_id)
        self._refresh()
        self.app.navigate("DetailsPage")

    def _export(self, project_id: str) -> None:
        self.app.open_project(project_id)
        self.app.navigate("ExportPage")

    def _duplicate(self, project_id: str) -> None:
        copy = self.app.library.duplicate(project_id)
        self.app.set_status(f"Duplicated as '{copy.display_name}'.")
        self._refresh()

    def _delete(self, project_id: str) -> None:
        from tkinter import messagebox

        try:
            project = self.app.library.load(project_id)
        except Exception:
            return
        if not messagebox.askyesno(
            "Delete project",
            f"Delete '{project.display_name}' and everything it produced?\n\n"
            "This cannot be undone.",
        ):
            return
        self.app.library.delete(project_id)
        if self.app.project is not None and self.app.project.id == project_id:
            self.app.project = None
        self.app.set_status("Project deleted.")
        self._refresh()
