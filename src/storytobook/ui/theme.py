"""Interface helpers: colours, fonts and reusable widgets."""

from __future__ import annotations

import customtkinter as ctk

#: Semantic colours used across the interface.
COLORS = {
    "bg": "#12131a",
    "surface": "#1b1d27",
    "surface_alt": "#232634",
    "border": "#2e3140",
    "text": "#e9e9f0",
    "muted": "#9a9db0",
    "accent": "#4c8dff",
    "accent_hover": "#3a7ae8",
    "success": "#3fb950",
    "warning": "#d29922",
    "danger": "#f85149",
}

#: Font sizes used in the interface.
SIZES = {
    "hero": 40,
    "title": 26,
    "subtitle": 18,
    "body": 14,
    "small": 12,
    "tiny": 11,
}


def apply_theme(mode: str = "dark", accent: str = "blue") -> None:
    """Apply the appearance mode and colour theme to customtkinter."""
    try:
        ctk.set_appearance_mode(mode if mode in {"dark", "light"} else "dark")
    except Exception:
        ctk.set_appearance_mode("dark")
    try:
        ctk.set_default_color_theme(accent if accent in _THEMES else "blue")
    except Exception:
        ctk.set_default_color_theme("blue")


_THEMES = {"blue", "green", "dark-blue", "light-blue"}


def font(size: int = 14, weight: str = "normal") -> ctk.CTkFont:
    """A themed font."""
    return ctk.CTkFont(size=size, weight=weight)


def title_font(size: int = 26) -> ctk.CTkFont:
    return ctk.CTkFont(family="Segoe UI", size=size, weight="bold")


def hero_font(size: int = 40) -> ctk.CTkFont:
    return ctk.CTkFont(family="Segoe UI", size=size, weight="bold")


def muted_font(size: int = 12) -> ctk.CTkFont:
    return ctk.CTkFont(size=size)


class SectionTitle(ctk.CTkFrame):
    """A heading with an optional subtitle, used at the top of each screen."""

    def __init__(self, master, title: str, subtitle: str = "", **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            self,
            text=title,
            font=title_font(SIZES["title"]),
            anchor="w",
            justify="left",
        ).grid(row=0, column=0, sticky="ew")
        if subtitle:
            ctk.CTkLabel(
                self,
                text=subtitle,
                font=muted_font(SIZES["body"]),
                text_color=COLORS["muted"],
                anchor="w",
                justify="left",
                wraplength=620,
            ).grid(row=1, column=0, sticky="ew", pady=(4, 0))


class Card(ctk.CTkFrame):
    """A rounded surface used to group content."""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", COLORS["surface"])
        kwargs.setdefault("corner_radius", 14)
        kwargs.setdefault("border_width", 1)
        kwargs.setdefault("border_color", COLORS["border"])
        super().__init__(master, **kwargs)


class Badge(ctk.CTkLabel):
    """A small pill that shows a project status."""

    STATUS_COLOURS = {
        "Draft": COLORS["muted"],
        "Audio recorded": COLORS["warning"],
        "Transcript ready": COLORS["accent"],
        "Cover ready": COLORS["accent"],
        "Published": COLORS["success"],
    }

    def __init__(self, master, text: str = "Draft", **kwargs):
        kwargs.setdefault("text_color", COLORS["muted"])
        kwargs.setdefault("font", muted_font(SIZES["tiny"]))
        kwargs.setdefault("corner_radius", 8)
        kwargs.setdefault("padx", 8)
        kwargs.setdefault("pady", 2)
        super().__init__(master, text=text, **kwargs)

    def set_status(self, label: str) -> None:
        self.configure(text=label, text_color=self.STATUS_COLOURS.get(label, COLORS["muted"]))


class StatTile(ctk.CTkFrame):
    """One number with a caption, shown on the dashboard."""

    def __init__(self, master, caption: str, value: str = "0", **kwargs):
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)
        self.grid_columnconfigure(0, weight=1)
        self.value_label = ctk.CTkLabel(
            self, text=value, font=title_font(24), anchor="w"
        )
        self.value_label.grid(row=0, column=0, sticky="ew")
        self.caption_label = ctk.CTkLabel(
            self, text=caption, font=muted_font(SIZES["small"]), text_color=COLORS["muted"], anchor="w"
        )
        self.caption_label.grid(row=1, column=0, sticky="ew")

    def set_value(self, value: str) -> None:
        self.value_label.configure(text=str(value))


class ScrollFrame(ctk.CTkScrollableFrame):
    """A scrollable frame with a consistent look."""

    def __init__(self, master, **kwargs):
        kwargs.setdefault("fg_color", "transparent")
        super().__init__(master, **kwargs)
