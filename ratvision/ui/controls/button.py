from __future__ import annotations

from collections.abc import Callable

from .base import ThemedCanvas, rounded_rect


class RatButton(ThemedCanvas):
    def __init__(self, master, *, text: str, command: Callable[[], None] | None, theme, width=180, height=38, danger=False):
        self.text = text
        self.command = command
        self.danger = danger
        self._hover = False
        super().__init__(master, theme=theme, width=width, height=height, cursor="hand2")
        self.bind("<Button-1>", self._on_click)
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.redraw()

    def _on_click(self, _event):
        if self.command:
            self.command()

    def _on_enter(self, _event):
        self._hover = True
        self.redraw()

    def _on_leave(self, _event):
        self._hover = False
        self.redraw()

    def redraw(self):
        self.delete("all")
        w = max(self.winfo_width(), int(self.cget("width")))
        h = max(self.winfo_height(), int(self.cget("height")))
        border = self.theme.danger if (self.danger and self._hover) else self.theme.border
        fill = self.theme.panel_alt if self._hover else self.theme.panel
        rounded_rect(self, 1, 1, w - 2, h - 2, 5, fill=fill, outline=border, width=1)
        self.create_text(14, h / 2, text=self.text, anchor="w", fill=self.theme.text, font=self.theme.font_ui)
