"""Settings screen."""

from __future__ import annotations

import customtkinter as ctk

from ... import paths
from ...providers.cover import list_cover_providers
from ...providers.transcription import list_transcription_providers
from ..system import open_path
from ..theme import COLORS, SIZES, Card, SectionTitle, font, muted_font
from .base import Page

WHISPER_SIZES = ["tiny", "base", "small", "medium", "large"]


class SettingsPage(Page):
    """Every knob the user can turn."""

    title = "Settings"

    def __init__(self, master, app):
        super().__init__(master, app)
        self.build()

    def build(self) -> None:
        wrapper = ctk.CTkFrame(self, fg_color="transparent")
        wrapper.grid(row=0, column=0, sticky="nsew")
        wrapper.grid_columnconfigure(0, weight=1)
        wrapper.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(wrapper, fg_color="transparent")
        header.grid(row=0, column=0, sticky="ew", padx=34, pady=(30, 0))
        header.grid_columnconfigure(0, weight=1)
        SectionTitle(
            header,
            "Settings",
            "Everything is stored on this machine. The built-in designer and the "
            "manual editor work with no extra downloads at all.",
        ).grid(row=0, column=0, sticky="ew")

        body = ctk.CTkScrollableFrame(wrapper, fg_color="transparent")
        body.grid(row=1, column=0, sticky="nsew", padx=26, pady=(18, 26))
        body.grid_columnconfigure(0, weight=1)

        self.body = body
        self._build_transcription(body)
        self._build_cover(body)
        self._build_writing(body)
        self._build_interface(body)
        self._build_storage(body)

        footer = ctk.CTkFrame(wrapper, fg_color="transparent")
        footer.grid(row=2, column=0, sticky="ew", padx=34, pady=(0, 24))
        footer.grid_columnconfigure(0, weight=1)

        self.feedback = ctk.CTkLabel(
            footer, text="", font=muted_font(SIZES["small"]), text_color=COLORS["success"], anchor="w"
        )
        self.feedback.grid(row=0, column=0, sticky="w")

        ctk.CTkButton(
            footer,
            text="Save settings",
            width=170,
            height=40,
            corner_radius=9,
            font=font(SIZES["body"], "bold"),
            command=self._save,
        ).grid(row=0, column=1, sticky="e")

    # ------------------------------------------------------------------ #
    # Sections
    # ------------------------------------------------------------------ #
    def _section(self, title: str, subtitle: str = "") -> ctk.CTkFrame:
        card = Card(self.body)
        card.grid_columnconfigure(0, weight=1)
        card.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(card, text=title, font=font(SIZES["subtitle"], "bold"), anchor="w").grid(
            row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(18, 2)
        )
        if subtitle:
            ctk.CTkLabel(
                card,
                text=subtitle,
                font=muted_font(SIZES["small"]),
                text_color=COLORS["muted"],
                anchor="w",
                wraplength=560,
                justify="left",
            ).grid(row=1, column=0, columnspan=2, sticky="ew", padx=20, pady=(0, 12))
        return card

    @staticmethod
    def _field(parent, row: int, label: str, widget, hint: str = "") -> None:
        ctk.CTkLabel(
            parent, text=label, font=muted_font(SIZES["small"]), text_color=COLORS["muted"]
        ).grid(row=row, column=0, sticky="w", padx=(20, 16), pady=8)
        widget.grid(row=row, column=1, sticky="ew", padx=(0, 20), pady=8)
        if hint:
            ctk.CTkLabel(
                parent,
                text=hint,
                font=muted_font(SIZES["tiny"]),
                text_color=COLORS["muted"],
                anchor="w",
                wraplength=380,
                justify="left",
            ).grid(row=row + 1, column=1, sticky="ew", padx=(0, 20), pady=(0, 6))

    def _build_transcription(self, parent) -> None:
        card = self._section(
            "Transcription",
            "Whisper runs locally and needs no account. The cloud option needs an API key.",
        )
        card.grid(row=0, column=0, sticky="ew", pady=(0, 14))

        providers = list_transcription_providers()
        labels = {p.name: p.label for p in providers}
        self.transcription_menu = ctk.CTkOptionMenu(card,
            values=list(labels.values()), height=34, corner_radius=8
        )
        self._field(card, 2, "Engine", self.transcription_menu)
        self._transcription_labels = labels

        self.whisper_menu = ctk.CTkOptionMenu(card, values=WHISPER_SIZES, height=34, corner_radius=8)
        self._field(card, 4, "Whisper model size", self.whisper_menu, "Larger models are more accurate but slower.")

        self.language_entry = ctk.CTkEntry(card, height=34, corner_radius=8, placeholder_text="auto")
        self._field(card, 6, "Language", self.language_entry, "Leave as 'auto' to detect the language.")

        self.api_key_entry = ctk.CTkEntry(card, height=34, corner_radius=8, show="*", placeholder_text="sk-...")
        self._field(card, 8, "OpenAI API key", self.api_key_entry, "Only needed for the cloud engine.")

    def _build_cover(self, parent) -> None:
        card = self._section(
            "Cover art",
            "The built-in designer always works. A local diffusion model gives richer artwork.",
        )
        card.grid(row=1, column=0, sticky="ew", pady=(0, 14))

        providers = [p for p in list_cover_providers() if p.name != "auto"]
        labels = {p.name: p.label for p in providers}
        self.cover_menu = ctk.CTkOptionMenu(card, values=list(labels.values()), height=34, corner_radius=8)
        self._field(card, 2, "Engine", self.cover_menu)
        self._cover_labels = labels

        self.base_model_entry = ctk.CTkEntry(card, height=34, corner_radius=8)
        self._field(
            card, 4, "Diffusion model", self.base_model_entry,
            "A checkpoint on Hugging Face, for example stable-diffusion-v1-5/stable-diffusion-v1-5.",
        )

        self.use_lora = ctk.CTkSwitch(card, text="Apply a LoRA adapter", font=muted_font(SIZES["small"]))
        self._field(card, 6, "LoRA", self.use_lora)

        self.lora_entry = ctk.CTkEntry(card, height=34, corner_radius=8, placeholder_text="C:\\models\\my-lora")
        self._field(
            card, 8, "Adapter folder", self.lora_entry,
            "The folder that holds adapter_config.json and adapter_model.safetensors.",
        )

        self.steps_entry = ctk.CTkEntry(card, width=100, height=34, corner_radius=8)
        self._field(card, 10, "Steps", self.steps_entry, "More steps means a slower, cleaner image.")

        self.guidance_entry = ctk.CTkEntry(card, width=100, height=34, corner_radius=8)
        self._field(card, 12, "Guidance", self.guidance_entry, "How closely the image follows the prompt.")

        self.size_entry = ctk.CTkEntry(card, width=180, height=34, corner_radius=8, placeholder_text="1200 x 1600")
        self._field(card, 14, "Cover size", self.size_entry, "Width x height in pixels.")

        self.prompt_entry = ctk.CTkEntry(card, height=34, corner_radius=8, placeholder_text="extra art direction")
        self._field(card, 16, "Extra prompt", self.prompt_entry)

    def _build_writing(self, parent) -> None:
        card = self._section("Writing", "How the transcript is divided into chapters.")
        card.grid(row=2, column=0, sticky="ew", pady=(0, 14))

        self.chapter_entry = ctk.CTkEntry(card, width=140, height=34, corner_radius=8)
        self._field(card, 2, "Chapter length (words)", self.chapter_entry)

    def _build_interface(self, parent) -> None:
        card = self._section("Interface")
        card.grid(row=3, column=0, sticky="ew", pady=(0, 14))

        self.appearance_menu = ctk.CTkOptionMenu(card,
            values=["dark", "light", "system"], height=34, corner_radius=8
        )
        self._field(card, 2, "Appearance", self.appearance_menu, "Light and dark changes apply after a restart.")

        self.accent_menu = ctk.CTkOptionMenu(card,
            values=["blue", "green", "dark-blue", "light-blue"], height=34, corner_radius=8
        )
        self._field(card, 4, "Accent colour", self.accent_menu)

    def _build_storage(self, parent) -> None:
        card = self._section("Storage", "Projects, recordings and exports live in this folder.")
        card.grid(row=4, column=0, sticky="ew", pady=(0, 14))

        ctk.CTkLabel(
            card,
            text=str(paths.data_dir()),
            font=muted_font(SIZES["small"]),
            text_color=COLORS["muted"],
            anchor="w",
        ).grid(row=2, column=0, sticky="w", padx=20, pady=8)
        ctk.CTkButton(
            card,
            text="Open folder",
            width=140,
            height=34,
            corner_radius=8,
            command=lambda: open_path(paths.data_dir()),
        ).grid(row=2, column=1, sticky="e", padx=20, pady=8)

    # ------------------------------------------------------------------ #
    def on_show(self, **kwargs) -> None:
        settings = self.app.settings

        label_to_name = {label: name for name, label in self._transcription_labels.items()}
        self.transcription_menu.set(label_to_name.get(settings.transcription_provider, "Whisper (local, offline)"))

        self.whisper_menu.set(settings.whisper_model_size)
        self.language_entry.delete(0, "end")
        self.language_entry.insert(0, settings.whisper_language)
        self.api_key_entry.delete(0, "end")
        self.api_key_entry.insert(0, settings.openai_api_key)

        label_to_name = {label: name for name, label in self._cover_labels.items()}
        self.cover_menu.set(label_to_name.get(settings.cover_provider, "Built-in designer (offline, instant)"))
        self.base_model_entry.delete(0, "end")
        self.base_model_entry.insert(0, settings.cover_base_model)
        self.use_lora.select() if settings.cover_use_lora else self.use_lora.deselect()
        self.lora_entry.delete(0, "end")
        self.lora_entry.insert(0, settings.cover_lora_path)
        self.steps_entry.delete(0, "end")
        self.steps_entry.insert(0, str(settings.cover_steps))
        self.guidance_entry.delete(0, "end")
        self.guidance_entry.insert(0, str(settings.cover_guidance_scale))
        self.size_entry.delete(0, "end")
        self.size_entry.insert(0, f"{settings.cover_width} x {settings.cover_height}")
        self.prompt_entry.delete(0, "end")
        self.prompt_entry.insert(0, settings.cover_extra_prompt)

        self.chapter_entry.delete(0, "end")
        self.chapter_entry.insert(0, str(settings.chapter_target_words))

        self.appearance_menu.set(settings.appearance_mode)
        self.accent_menu.set(settings.accent_color)
        self._original_appearance = settings.appearance_mode
        self.feedback.configure(text="")

    # ------------------------------------------------------------------ #
    def _save(self) -> None:
        settings = self.app.settings

        name_to_label = {name: label for name, label in self._transcription_labels.items()}
        selected = self.transcription_menu.get()
        for name, label in name_to_label.items():
            if label == selected:
                settings.transcription_provider = name

        name_to_label = {name: label for name, label in self._cover_labels.items()}
        selected = self.cover_menu.get()
        for name, label in name_to_label.items():
            if label == selected:
                settings.cover_provider = name

        settings.whisper_model_size = self.whisper_menu.get()
        settings.whisper_language = self.language_entry.get().strip() or "auto"
        settings.openai_api_key = self.api_key_entry.get().strip()
        settings.cover_base_model = self.base_model_entry.get().strip()
        settings.cover_use_lora = bool(self.use_lora.get())
        settings.cover_lora_path = self.lora_entry.get().strip()
        settings.cover_extra_prompt = self.prompt_entry.get().strip()

        try:
            settings.cover_steps = int(self.steps_entry.get().strip())
        except ValueError:
            settings.cover_steps = 30
        try:
            settings.cover_guidance_scale = float(self.guidance_entry.get().strip())
        except ValueError:
            settings.cover_guidance_scale = 7.5

        size = self.size_entry.get().strip().lower().replace("×", "x").split("x")
        try:
            if len(size) == 2:
                settings.cover_width = int(size[0].strip())
                settings.cover_height = int(size[1].strip())
        except ValueError:
            pass

        try:
            settings.chapter_target_words = int(self.chapter_entry.get().strip())
        except ValueError:
            settings.chapter_target_words = 1000

        settings.appearance_mode = self.appearance_menu.get()
        settings.accent_color = self.accent_menu.get()

        settings.sanitise()
        settings.save()
        self.app.set_status("Settings saved.")

        if settings.appearance_mode != getattr(self, "_original_appearance", settings.appearance_mode):
            self.feedback.configure(text="Saved. Restart the app to apply the new appearance.")
        else:
            self.feedback.configure(text="Settings saved.")
