from __future__ import annotations

import tkinter as tk


class RatCard(tk.Frame):
    def __init__(self, master, *, theme, **kwargs):
        self.theme = theme
        kwargs.setdefault("background", theme.panel)
        kwargs.setdefault("highlightthickness", 1)
        kwargs.setdefault("highlightbackground", theme.border)
        kwargs.setdefault("bd", 0)
        super().__init__(master, **kwargs)

    def set_theme(self, theme) -> None:
        self.theme = theme
        self.configure(background=theme.panel, highlightbackground=theme.border)
