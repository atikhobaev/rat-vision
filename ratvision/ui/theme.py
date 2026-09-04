from __future__ import annotations

from dataclasses import dataclass
import sys
import tkinter as tk
from tkinter import ttk

from ratvision.domain.models import ThemeMode


@dataclass(frozen=True, slots=True)
class ThemeTokens:
    mode: ThemeMode
    background: str
    sidebar: str
    panel: str
    panel_alt: str
    text: str
    text_muted: str
    border: str
    accent: str
    accent_soft: str
    status_on: str
    status_off: str
    danger: str
    track: str
    slider_active: str
    font_ui: tuple[str, int]
    font_small: tuple[str, int]
    font_mono: tuple[str, int]
    font_display: tuple[str, int, str]


_NIGHT = ThemeTokens(
    mode=ThemeMode.NIGHT,
    background="#070809",
    sidebar="#0B0D0E",
    panel="#111315",
    panel_alt="#15181A",
    text="#E7E9E7",
    text_muted="#899197",
    border="#2D3337",
    accent="#D9DCDA",
    accent_soft="#23282B",
    status_on="#39FF74",
    status_off="#555C61",
    danger="#C9665C",
    track="#3B4246",
    slider_active="#D9DCDA",
    font_ui=("Segoe UI", 10),
    font_small=("Segoe UI", 9),
    font_mono=("Consolas", 9),
    font_display=("Arial Narrow", 12, "bold"),
)

_DAY = ThemeTokens(
    mode=ThemeMode.DAY,
    background="#F3F5F6",
    sidebar="#E9EFF2",
    panel="#FFFFFF",
    panel_alt="#F8FAFB",
    text="#17191B",
    text_muted="#616A70",
    border="#CCD4D8",
    accent="#39AEEA",
    accent_soft="#E8F6FB",
    status_on="#25C962",
    status_off="#9AA2A7",
    danger="#B94B42",
    track="#CAD2D6",
    slider_active="#39AEEA",
    font_ui=("Segoe UI", 10),
    font_small=("Segoe UI", 9),
    font_mono=("Consolas", 9),
    font_display=("Arial Narrow", 12, "bold"),
)


def _resolve_windows_theme() -> ThemeMode:
    if sys.platform != "win32":
        return ThemeMode.NIGHT
    try:
        import winreg
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
        ) as key:
            value, _kind = winreg.QueryValueEx(key, "AppsUseLightTheme")
        return ThemeMode.DAY if int(value) else ThemeMode.NIGHT
    except (OSError, ValueError, TypeError):
        return ThemeMode.NIGHT


class ThemeManager:
    def __init__(self, *, system_theme_resolver=None) -> None:
        self._system_theme_resolver = system_theme_resolver or _resolve_windows_theme
        self.current = _NIGHT

    def tokens(self, mode: ThemeMode) -> ThemeTokens:
        if mode == ThemeMode.SYSTEM:
            mode = ThemeMode(self._system_theme_resolver())
        if mode == ThemeMode.DAY:
            return _DAY
        return _NIGHT

    def apply(self, root: tk.Misc, mode: ThemeMode) -> ThemeTokens:
        self.current = self.tokens(mode)
        root.configure(background=self.current.background)
        style = ttk.Style(root)
        style.configure("Rat.TFrame", background=self.current.background)
        style.configure("RatPanel.TFrame", background=self.current.panel)
        style.configure(
            "Rat.TLabel",
            background=self.current.background,
            foreground=self.current.text,
            font=self.current.font_ui,
        )
        style.configure(
            "RatMuted.TLabel",
            background=self.current.background,
            foreground=self.current.text_muted,
            font=self.current.font_small,
        )
        style.configure(
            "Rat.TEntry",
            fieldbackground=self.current.panel,
            foreground=self.current.text,
        )
        return self.current
