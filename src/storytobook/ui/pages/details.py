"""Book details: title page metadata and cover art."""

from __future__ import annotations

import customtkinter as ctk
from PIL import Image

from ..theme import COLORS, SIZES, Card, SectionTitle, font, muted_font
from .base import Page

COVER_PREVIEW = (260, 346)


class DetailsPage(Page):
    """Collects the front-matter of the book and renders the cover."""

    title = "Details"

    def __init__(self, master, app):
        super().__init__(master, app)
        self._preview_image = None
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
            "Book details",
            "These details appear on the title page, the cover and the colophon.",
        ).grid(row=0, column=0, sticky="ew")

        # --- left: form ------------------------------------------------ #
        left = ctk.CTkFrame(wrapper, fg_color="transparent")
        left.grid(row=1, column=0, sticky="nsew", padx=(34, 10), pady=(18, 26))
        left.grid_columnconfigure(0, weight=1)
        left.grid_rowconfigure(10, weight=1)

        self.title_entry = self._labelled_entry(left, 0, "Book title", "The Quiet Harbour")
        self.author_entry = self._labelled_entry(left, 2, "Author", "Ada Marlowe")
        self.publisher_entry = self._labelled_entry(left, 4, "Publisher (optional)", "Lantern Press")

        ctk.CTkLabel(
            left, text="Acknowledgment (optional)", font=muted_font(SIZES["small"]), text_color=COLORS["muted"]
        ).grid(row=6, column=0, sticky="w", pady=(14, 4))
        self.ack_box = ctk.CTkTextbox(left, height=90, corner_radius=10, wrap="word")
        self.ack_box.grid(row=7, column=0, sticky="ew")

        ctk.CTkLabel(
            left, text="Author's note (optional)", font=muted_font(SIZES["small"]), text_color=COLORS["muted"]
        ).grid(row=8, column=0, sticky="w", pady=(14, 4))
        self.note_box = ctk.CTkTextbox(left, height=90, corner_radius=10, wrap="word")
        self.note_box.grid(row=9, column=0, sticky="ew")

        # --- right: cover ---------------------------------------------- #
        right = Card(wrapper)
        right.grid(row=1, column=1, sticky="nsew", padx=(10, 34), pady=(18, 26))
        right.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            right, text="Cover", font=font(SIZES["subtitle"], "bold"), anchor="w"
        ).grid(row=0, column=0, sticky="ew", padx=20, pady=(18, 4))

        self.cover_label = ctk.CTkLabel(
            right, text="No cover yet", font=muted_font(SIZES["small"]), text_color=COLORS["muted"]
        )
        self.cover_label.grid(row=1, column=0, sticky="ew", padx=20)

        self.provider_label = ctk.CTkLabel(
            right, text="", font=muted_font(SIZES["tiny"]), text_color=COLORS["muted"], anchor="w"
        )
        self.provider_label.grid(row=2, column=0, sticky="ew", padx=20, pady=(10, 0))

        self.cover_button = ctk.CTkButton(
            right,
            text="Generate cover",
            width=200,
            height=40,
            corner_radius=9,
            command=self._generate_cover,
        )
        self.cover_button.grid(row=3, column=0, sticky="w", padx=20, pady=(12, 0))

        self.cover_progress = ctk.CTkProgressBar(right, height=6, corner_radius=3)
        self.cover_progress.grid(row=4, column=0, sticky="ew", padx=20, pady=(12, 0))
        self.cover_progress.set(0)

        self.cover_status = ctk.CTkLabel(
            right,
            text="",
            font=muted_font(SIZES["small"]),
            text_color=COLORS["muted"],
            anchor="w",
            wraplength=280,
            justify="left",
        )
        self.cover_status.grid(row=5, column=0, sticky="ew", padx=20, pady=(8, 0))

        # --- footer ---------------------------------------------------- #
        footer = ctk.CTkFrame(wrapper, fg_color="transparent")
        footer.grid(row=2, column=0, columnspan=2, sticky="ew", padx=34, pady=(0, 24))
        footer.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(
            footer,
            text="Back to the story",
            width=180,
            height=40,
            corner_radius=9,
            fg_color="transparent",
            border_width=1,
            border_color=COLORS["border"],
            text_color=COLORS["muted"],
            hover_color=COLORS["surface_alt"],
            command=lambda: self.app.navigate("TranscriptPage"),
        ).grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            footer,
            text="Continue to export",
            width=200,
            height=40,
            corner_radius=9,
            font=font(SIZES["body"], "bold"),
            command=self._continue,
        ).grid(row=0, column=2, sticky="e")

    # ------------------------------------------------------------------ #
    def _labelled_entry(self, parent, row: int, label: str, placeholder: str) -> ctk.CTkEntry:
        """A label with an entry underneath it.  ``row`` is the label's row."""
        ctk.CTkLabel(
            parent, text=label, font=muted_font(SIZES["small"]), text_color=COLORS["muted"]
        ).grid(row=row, column=0, sticky="w", pady=(14 if row else 0, 4))
        entry = ctk.CTkEntry(parent, height=36, corner_radius=9, placeholder_text=placeholder)
        entry.grid(row=row + 1, column=0, sticky="ew")
        return entry

    # ------------------------------------------------------------------ #
    def on_show(self, **kwargs) -> None:
        project = self.app.project
        if project is None:
            self.app.set_status("Open a project first.")
            self.app.navigate("DashboardPage")
            return

        self.title_entry.delete(0, "end")
        self.title_entry.insert(0, project.title)
        self.author_entry.delete(0, "end")
        self.author_entry.insert(0, project.author)
        self.publisher_entry.delete(0, "end")
        self.publisher_entry.insert(0, project.publisher)

        self.ack_box.delete("1.0", "end")
        self.ack_box.insert("1.0", project.acknowledgment)
        self.note_box.delete("1.0", "end")
        self.note_box.insert("1.0", project.author_note)

        self._refresh_cover()

    # ------------------------------------------------------------------ #
    def _refresh_cover(self) -> None:
        project = self.app.project
        if project is None:
            return
        cover = self.app.library.cover_path(project.id)
        if not cover.exists():
            self.cover_label.configure(image=None, text="No cover yet")
            self._preview_image = None
            return
        try:
            image = Image.open(cover).convert("RGB")
        except OSError:
            return
        image.thumbnail(COVER_PREVIEW, Image.LANCZOS)
        # CTkImage keeps the preview sharp on high-DPI screens.
        self._preview_image = ctk.CTkImage(
            light_image=image, dark_image=image, size=image.size
        )
        self.cover_label.configure(image=self._preview_image, text="")

    def _provider_text(self) -> str:
        from ...providers.cover import build_cover_provider

        provider = build_cover_provider(self.app.settings.cover_provider, self.app.settings)
        return provider.label

    # ------------------------------------------------------------------ #
    def _collect(self) -> bool:
        project = self.app.project
        if project is None:
            return False
        project.title = self.title_entry.get().strip() or "Untitled Story"
        project.author = self.author_entry.get().strip()
        project.publisher = self.publisher_entry.get().strip()
        project.acknowledgment = self.ack_box.get("1.0", "end-1c").strip()
        project.author_note = self.note_box.get("1.0", "end-1c").strip()
        self.app.library.save(project)
        return True

    def _generate_cover(self) -> None:
        if not self.app.require_project():
            return
        if not self._collect():
            return

        project = self.app.project
        pipeline = self.app.pipeline
        self.cover_button.configure(state="disabled", text="Working...")
        self.cover_progress.set(0.05)
        self.cover_status.configure(text="Starting...")

        def work(report):
            return pipeline.generate_cover(project, report)

        def on_done(_result):
            self.cover_button.configure(state="normal", text="Regenerate cover")
            self.cover_progress.set(1.0)
            self.cover_status.configure(text="Cover ready.")
            self._refresh_cover()
            self.app.set_status("Cover generated.")

        def on_error(error):
            self.cover_button.configure(state="normal", text="Generate cover")
            self.cover_status.configure(text=str(error), text_color=COLORS["danger"])
            self.app.set_status(str(error))
            hint = getattr(error, "hint", "")
            if hint:
                self.cover_status.configure(text=f"{error}\n{hint}")

        self.app.run_background(work, on_done=on_done, on_error=on_error, status="Creating the cover...")

    def _continue(self) -> None:
        if not self._collect():
            return
        self.app.navigate("ExportPage")
