"""Welcome screen."""

from __future__ import annotations

import customtkinter as ctk

from ..theme import COLORS, SIZES, Card, font, hero_font, muted_font
from .base import Page


class LandingPage(Page):
    """The first thing the user sees."""

    title = "Home"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.build()

    def build(self) -> None:
        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.grid(row=0, column=0, sticky="nsew")
        wrapper.grid_columnconfigure(0, weight=1)
        wrapper.grid_rowconfigure(1, weight=1)

        hero = ctk.CTkFrame(wrapper, fg_color="transparent")
        hero.grid(row=0, column=0, pady=(70, 10))
        ctk.CTkLabel(
            hero, text="Your voice, bound.", font=hero_font(SIZES["hero"]), anchor="w"
        ).pack(anchor="w")
        ctk.CTkLabel(
            hero,
            text="Record a story, let StoryToBook transcribe and typeset it, and walk away with a finished book.",
            font=font(SIZES["subtitle"]),
            text_color=COLORS["muted"],
            anchor="w",
            justify="left",
            wraplength=560,
        ).pack(anchor="w", pady=(10, 26))

        actions = ctk.CTkFrame(hero, fg_color="transparent")
        actions.pack(anchor="w")
        ctk.CTkButton(
            actions,
            text="Start a new book",
            width=200,
            height=44,
            corner_radius=10,
            font=font(SIZES["body"], "bold"),
            command=self._new_book,
        ).pack(side="left")
        ctk.CTkButton(
            actions,
            text="Open my library",
            width=180,
            height=44,
            corner_radius=10,
            fg_color="transparent",
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["text"],
            hover_color=COLORS["surface_alt"],
            command=lambda: self.app.navigate("DashboardPage"),
        ).pack(side="left", padx=10)

        # Status of the optional AI engines.
        status = Card(wrapper)
        status.grid(row=2, column=0, sticky="ew", pady=(36, 0))
        status.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(
            status,
            text="Engines",
            font=font(SIZES["small"], "bold"),
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=0, column=0, sticky="ew", padx=18, pady=(14, 6))

        self.engine_list = ctk.CTkFrame(status, fg_color="transparent")
        self.engine_list.grid(row=1, column=0, sticky="ew", padx=18, pady=(0, 16))
        self.engine_list.grid_columnconfigure(0, weight=1)

    # ------------------------------------------------------------------ #
    def on_show(self, **kwargs) -> None:
        self._refresh_engines()

    def _refresh_engines(self) -> None:
        from ...providers.cover import list_cover_providers
        from ...providers.transcription import list_transcription_providers

        for child in self.engine_list.winfo_children():
            child.destroy()

        entries: list[tuple[str, str, bool]] = []
        for provider in list_transcription_providers():
            entries.append(("Transcription", provider.label, provider.is_available()))
        for provider in list_cover_providers():
            if provider.name == "auto":
                continue
            entries.append(("Cover art", provider.label, provider.is_available()))

        for index, (kind, label, available) in enumerate(entries):
            row = ctk.CTkFrame(self.engine_list, fg_color="transparent")
            row.grid(row=index, column=0, sticky="ew", pady=2)
            row.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(
                row, text=kind, font=muted_font(SIZES["tiny"]), text_color=COLORS["muted"], width=90, anchor="w"
            ).grid(row=0, column=0, sticky="w")
            ctk.CTkLabel(row, text=label, font=muted_font(SIZES["small"]), anchor="w").grid(
                row=0, column=1, sticky="w"
            )
            ctk.CTkLabel(
                row,
                text="Ready" if available else "Not installed",
                font=muted_font(SIZES["tiny"]),
                text_color=COLORS["success"] if available else COLORS["warning"],
                anchor="e",
            ).grid(row=0, column=2, sticky="e")

    # ------------------------------------------------------------------ #
    def _new_book(self) -> None:
        if self.app.project is not None:
            self.app.save_project()
        self.app.new_project(title="Untitled Story")
        self.app.navigate("RecordingPage")
