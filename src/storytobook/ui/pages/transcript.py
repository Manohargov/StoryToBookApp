"""Transcript screen: edit the text and shape the chapters."""

from __future__ import annotations

import customtkinter as ctk

from ...domain.chapter import Chapter, build_chapters
from ...domain.text import estimate_reading_minutes, word_count
from ..theme import COLORS, SIZES, Card, SectionTitle, font, muted_font
from .base import Page


class TranscriptPage(Page):
    """Shows the transcript and the chapters derived from it."""

    title = "Story"

    def __init__(self, master, app):
        super().__init__(master, app)
        self._loaded_text = ""
        self.build()

    def build(self) -> None:
        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.grid(row=0, column=0, sticky="nsew")
        wrapper.grid_columnconfigure(0, weight=3)
        wrapper.grid_columnconfigure(1, weight=2)
        wrapper.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(wrapper, fg_color="transparent")
        header.grid(row=0, column=0, columnspan=2, sticky="ew", padx=34, pady=(30, 0))
        header.grid_columnconfigure(0, weight=1)
        SectionTitle(
            header,
            "Your story",
            "Fix the wording, then decide how the book should be divided. "
            "Changes are saved to the project automatically.",
        ).grid(row=0, column=0, sticky="ew")

        # --- left: transcript ------------------------------------------ #
        left = ctk.CTkFrame(wrapper, fg_color="transparent")
        left.grid(row=1, column=0, sticky="nsew", padx=(34, 10), pady=(18, 26))
        left.grid_rowconfigure(1, weight=1)
        left.grid_columnconfigure(0, weight=1)

        stats = ctk.CTkFrame(left, fg_color="transparent")
        stats.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        stats.grid_columnconfigure(0, weight=1)

        self.stats_label = ctk.CTkLabel(
            stats, text="", font=muted_font(SIZES["small"]), text_color=COLORS["muted"], anchor="w"
        )
        self.stats_label.grid(row=0, column=0, sticky="w")

        self.text_box = ctk.CTkTextbox(
            left, wrap="word", corner_radius=12, border_width=1, border_color=COLORS["border"]
        )
        self.text_box.grid(row=1, column=0, sticky="nsew")
        self.text_box.bind("<KeyRelease>", lambda _e: self._on_text_changed())

        # --- right: chapters ------------------------------------------- #
        right = Card(wrapper)
        right.grid(row=1, column=1, sticky="nsew", padx=(10, 34), pady=(18, 26))
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            right,
            text="Chapters",
            font=font(SIZES["subtitle"], "bold"),
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=18, pady=(18, 10))

        tools = ctk.CTkFrame(right, fg_color="transparent")
        tools.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 10))
        tools.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            tools, text="Target length", font=muted_font(SIZES["small"]), text_color=COLORS["muted"]
        ).grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.target_entry = ctk.CTkEntry(tools, width=80, height=32, corner_radius=8)
        self.target_entry.grid(row=0, column=1, sticky="w")
        ctk.CTkLabel(
            tools, text="words", font=muted_font(SIZES["small"]), text_color=COLORS["muted"]
        ).grid(row=0, column=2, sticky="w", padx=(6, 0))

        ctk.CTkButton(
            tools,
            text="Re-split",
            width=92,
            height=32,
            corner_radius=8,
            command=self._resplit,
        ).grid(row=0, column=3, sticky="e")

        self.chapter_list = ctk.CTkScrollableFrame(right, fg_color="transparent")
        self.chapter_list.grid(row=2, column=0, sticky="nsew", padx=14, pady=(0, 8))
        self.chapter_list.grid_columnconfigure(0, weight=1)

        footer = ctk.CTkFrame(wrapper, fg_color="transparent")
        footer.grid(row=2, column=0, columnspan=2, sticky="ew", padx=34, pady=(0, 24))
        footer.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            footer,
            text="Back to recording",
            width=170,
            height=40,
            corner_radius=9,
            fg_color="transparent",
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["muted"],
            hover_color=COLORS["surface_alt"],
            command=lambda: self.app.navigate("RecordingPage"),
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            footer,
            text="Continue to book details",
            width=220,
            height=40,
            corner_radius=9,
            font=font(SIZES["body"], "bold"),
            command=self._continue,
        ).grid(row=0, column=2, sticky="e")

    # ------------------------------------------------------------------ #
    def on_show(self, manual: bool = False, **kwargs) -> None:
        project = self.app.project
        if project is None:
            self.app.set_status("Open a project first.")
            self.app.navigate("DashboardPage")
            return

        if manual or not project.transcript:
            self.text_box.delete("1.0", "end")
            if project.transcript:
                self.text_box.insert("1.0", project.transcript)
            self._loaded_text = ""
            self.app.set_status("Type or paste your story, then continue.")
        else:
            if self.text_box.get("1.0", "end-1c") != project.transcript:
                self.text_box.delete("1.0", "end")
                self.text_box.insert("1.0", project.transcript)
            self._loaded_text = project.transcript

        self.target_entry.delete(0, "end")
        self.target_entry.insert(0, str(self.app.settings.chapter_target_words))

        self._update_stats()
        self._refresh_chapters()

    # ------------------------------------------------------------------ #
    def _on_text_changed(self) -> None:
        self._update_stats()

    def _update_stats(self) -> None:
        text = self.text_box.get("1.0", "end-1c")
        words = word_count(text)
        minutes = estimate_reading_minutes(text) if words else 0
        self.stats_label.configure(
            text=f"{words:,} words  ·  ~{minutes} min read  ·  {len(text):,} characters"
        )

    def _current_text(self) -> str:
        return self.text_box.get("1.0", "end-1c").strip()

    def _resplit(self) -> None:
        project = self.app.project
        if project is None:
            return
        text = self._current_text()
        if not text:
            self.app.set_status("There is no text to split.")
            return

        try:
            target = int(self.target_entry.get().strip() or self.app.settings.chapter_target_words)
        except ValueError:
            target = self.app.settings.chapter_target_words
        target = max(100, target)

        project.transcript = text
        project.chapters = build_chapters(text, target)
        self.app.settings.chapter_target_words = target
        self.app.library.save(project)
        self._refresh_chapters()
        self.app.set_status(f"Rebuilt {len(project.chapters)} chapters.")

    def _refresh_chapters(self) -> None:
        project = self.app.project
        chapters = project.chapters if project else []

        for child in self.chapter_list.winfo_children():
            child.destroy()

        if not chapters:
            ctk.CTkLabel(
                self.chapter_list,
                text="No chapters yet. Use 'Re-split' once there is some text.",
                font=muted_font(SIZES["small"]),
                text_color=COLORS["muted"],
                wraplength=300,
                justify="left",
            ).grid(row=0, column=0, sticky="w", padx=6, pady=8)
            return

        for index, chapter in enumerate(chapters):
            self._add_chapter_row(index, chapter)

    def _add_chapter_row(self, index: int, chapter: Chapter) -> None:
        row = ctk.CTkFrame(self.chapter_list, fg_color="transparent")
        row.grid(row=index, column=0, sticky="ew", pady=4)
        row.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            row,
            text=f"{index + 1}",
            font=muted_font(SIZES["small"]),
            text_color=COLORS["muted"],
            width=22,
        ).grid(row=0, column=0, sticky="w")

        title_entry = ctk.CTkEntry(row, height=32, corner_radius=8, border_color=COLORS["border"])
        title_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        title_entry.insert(0, chapter.title)
        title_entry.bind(
            "<FocusOut>",
            lambda _e, entry=title_entry, ch=chapter: self._rename(ch, entry.get()),
        )
        title_entry.bind(
            "<Return>",
            lambda _e, entry=title_entry, ch=chapter: self._rename(ch, entry.get()),
        )

        ctk.CTkLabel(
            row,
            text=f"{chapter.word_count:,}w",
            font=muted_font(SIZES["tiny"]),
            text_color=COLORS["muted"],
            width=46,
        ).grid(row=0, column=2, sticky="e", padx=(0, 4))

        ctk.CTkButton(
            row,
            text="▲",
            width=28,
            height=28,
            corner_radius=7,
            fg_color="transparent",
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["muted"],
            hover_color=COLORS["surface_alt"],
            command=lambda i=index: self._move(i, -1),
        ).grid(row=0, column=3, padx=2)
        ctk.CTkButton(
            row,
            text="▼",
            width=28,
            height=28,
            corner_radius=7,
            fg_color="transparent",
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["muted"],
            hover_color=COLORS["surface_alt"],
            command=lambda i=index: self._move(i, 1),
        ).grid(row=0, column=4, padx=2)
        ctk.CTkButton(
            row,
            text="✕",
            width=28,
            height=28,
            corner_radius=7,
            fg_color="transparent",
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["danger"],
            hover_color=COLORS["surface_alt"],
            command=lambda i=index: self._remove(i),
        ).grid(row=0, column=5, padx=(2, 0))

    # ------------------------------------------------------------------ #
    def _rename(self, chapter: Chapter, value: str) -> None:
        chapter.title = value.strip()
        self.app.save_project()

    def _move(self, index: int, offset: int) -> None:
        project = self.app.project
        if project is None:
            return
        chapters = project.chapters
        target = index + offset
        if target < 0 or target >= len(chapters):
            return
        chapters[index], chapters[target] = chapters[target], chapters[index]
        self.app.library.save(project)
        self._refresh_chapters()

    def _remove(self, index: int) -> None:
        project = self.app.project
        if project is None:
            return
        del project.chapters[index]
        self.app.library.save(project)
        self._refresh_chapters()

    def _continue(self) -> None:
        project = self.app.project
        if project is None:
            return
        text = self._current_text()
        if text and text != project.transcript:
            project.transcript = text
            if not project.chapters:
                project.chapters = build_chapters(text, self.app.settings.chapter_target_words)
        self.app.library.save(project)
        self.app.navigate("DetailsPage")
