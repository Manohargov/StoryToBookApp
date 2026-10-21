"""Export screen: build the finished book."""

from __future__ import annotations

from pathlib import Path

import customtkinter as ctk

from ...exporters.registry import list_exporters
from ..system import open_path, reveal_in_file_manager
from ..theme import COLORS, SIZES, Card, SectionTitle, font, muted_font
from .base import Page


class ExportPage(Page):
    """Renders the book to the chosen format."""

    title = "Export"

    def __init__(self, master, app):
        super().__init__(master, app)
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
            "Publish",
            "Choose a format. The file is written into the project's export folder.",
        ).grid(row=0, column=0, sticky="ew")

        # --- format choice --------------------------------------------- #
        options = Card(wrapper)
        options.grid(row=1, column=0, sticky="ew", padx=34, pady=(18, 0))
        options.grid_columnconfigure(0, weight=1)

        self.format_buttons: dict[str, ctk.CTkButton] = {}
        row = ctk.CTkFrame(options, fg_color="transparent")
        row.grid(row=0, column=0, sticky="ew", padx=20, pady=18)
        row.grid_columnconfigure(0, weight=1)

        for index, exporter in enumerate(list_exporters()):
            button = ctk.CTkButton(
                row,
                text=f"{exporter.label}\n{exporter.extension}",
                width=180,
                height=58,
                corner_radius=10,
                fg_color="transparent",
                border_width=1,
                border_color=COLORS["border"],
                text_color=COLORS["muted"],
                hover_color=COLORS["surface_alt"],
                command=lambda name=exporter.name: self._select_format(name),
            )
            button.grid(row=0, column=index, sticky="w", padx=(0, 10))
            self.format_buttons[exporter.name] = button

        self.selected_format = self.app.settings.default_export_format
        self._select_format(self.selected_format)

        self.build_button = ctk.CTkButton(
            options,
            text="Build my book",
            width=200,
            height=44,
            corner_radius=10,
            font=font(SIZES["body"], "bold"),
            command=self._build,
        )
        self.build_button.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 18))

        self.progress = ctk.CTkProgressBar(options, height=8, corner_radius=4)
        self.progress.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 8))
        self.progress.set(0)
        self.progress.grid_remove()

        self.status_label = ctk.CTkLabel(
            options, text="", font=muted_font(SIZES["small"]), text_color=COLORS["muted"], anchor="w"
        )
        self.status_label.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 18))

        # --- produced files --------------------------------------------- #
        self.files_frame = ctk.CTkScrollableFrame(wrapper, fg_color="transparent")
        self.files_frame.grid(row=2, column=0, sticky="nsew", padx=26, pady=(16, 26))
        self.files_frame.grid_columnconfigure(0, weight=1)

        footer = ctk.CTkFrame(wrapper, fg_color="transparent")
        footer.grid(row=3, column=0, sticky="ew", padx=34, pady=(0, 24))
        footer.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            footer,
            text="Back to details",
            width=170,
            height=40,
            corner_radius=9,
            fg_color="transparent",
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["muted"],
            hover_color=COLORS["surface_alt"],
            command=lambda: self.app.navigate("DetailsPage"),
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            footer,
            text="Back to library",
            width=180,
            height=40,
            corner_radius=9,
            font=font(SIZES["body"], "bold"),
            command=lambda: self.app.navigate("DashboardPage"),
        ).grid(row=0, column=2, sticky="e")

    # ------------------------------------------------------------------ #
    def on_show(self, **kwargs) -> None:
        self._refresh_files()

    def _select_format(self, name: str) -> None:
        self.selected_format = name
        for key, button in self.format_buttons.items():
            active = key == name
            button.configure(
                fg_color=COLORS["accent"] if active else "transparent",
                text_color="#ffffff" if active else COLORS["muted"],
                border_color=COLORS["accent"] if active else COLORS["border"],
            )

    # ------------------------------------------------------------------ #
    def _build(self) -> None:
        if not self.app.require_project():
            return
        project = self.app.project
        pipeline = self.app.pipeline
        export_format = self.selected_format

        if not project.chapters and not project.transcript:
            self.status_label.configure(
                text="There is nothing to publish yet. Record or type your story first.",
                text_color=COLORS["warning"],
            )
            return

        self.build_button.configure(state="disabled", text="Building...")
        self.progress.grid()
        self.progress.set(0.1)
        self.status_label.configure(text="Building your book...", text_color=COLORS["muted"])

        def work(report):
            return pipeline.export(project, export_format, report)

        def on_done(result):
            self.build_button.configure(state="normal", text="Build my book")
            self.progress.set(1.0)
            self.status_label.configure(text=f"Saved to {Path(result).name}", text_color=COLORS["success"])
            self._refresh_files()
            self.app.set_status("Your book is ready.")

        def on_error(error):
            self.build_button.configure(state="normal", text="Build my book")
            self.progress.grid_remove()
            self.status_label.configure(text=str(error), text_color=COLORS["danger"])
            self.app.set_status(str(error))

        self.app.run_background(work, on_done=on_done, on_error=on_error, status="Building your book...")

    # ------------------------------------------------------------------ #
    def _refresh_files(self) -> None:
        for child in self.files_frame.winfo_children():
            child.destroy()

        project = self.app.project
        if project is None:
            return

        exports = list(reversed(project.exports))
        if not exports:
            ctk.CTkLabel(
                self.files_frame,
                text="Nothing has been exported for this project yet.",
                font=muted_font(SIZES["small"]),
                text_color=COLORS["muted"],
                anchor="w",
            ).grid(row=0, column=0, sticky="w", padx=8, pady=6)
            return

        for index, entry in enumerate(exports):
            path = Path(entry.get("path", ""))
            row = Card(self.files_frame)
            row.grid(row=index, column=0, sticky="ew", padx=4, pady=4)
            row.grid_columnconfigure(1, weight=1)

            ctk.CTkLabel(
                row,
                text=path.name,
                font=font(SIZES["body"], "bold"),
                anchor="w",
            ).grid(row=0, column=1, sticky="ew", padx=18, pady=(14, 0))

            size_kb = int(entry.get("size", 0)) // 1024
            ctk.CTkLabel(
                row,
                text=f"{entry.get('format', '').upper()}  ·  {size_kb} KB",
                font=muted_font(SIZES["tiny"]),
                text_color=COLORS["muted"],
                anchor="w",
            ).grid(row=1, column=1, sticky="ew", padx=18, pady=(0, 14))

            actions = ctk.CTkFrame(row, fg_color="transparent")
            actions.grid(row=0, column=2, rowspan=2, sticky="e", padx=18)
            ctk.CTkButton(
                actions,
                text="Open",
                width=76,
                height=32,
                corner_radius=8,
                command=lambda p=path: open_path(p),
            ).pack(side="left", padx=(0, 6))
            ctk.CTkButton(
                actions,
                text="Show",
                width=76,
                height=32,
                corner_radius=8,
                fg_color="transparent",
                border_width=1,
                border_color=COLORS["border"],
                text_color=COLORS["muted"],
                hover_color=COLORS["surface_alt"],
                command=lambda p=path: reveal_in_file_manager(p),
            ).pack(side="left")
