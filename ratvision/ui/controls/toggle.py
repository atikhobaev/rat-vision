from __future__ import annotations

from collections.abc import Callable

from .base import ThemedCanvas, rounded_rect


class RatToggle(ThemedCanvas):
    def __init__(self, master, *, value: bool, command: Callable[[bool], None] | None, theme, width=90, height=32):
        self.value = bool(value)
        self.command = command
        super().__init__(master, theme=theme, width=width, height=height, cursor="hand2")
        self.bind("<Button-1>", self._on_click)
        self.redraw()

    def set(self, value: bool, *, notify: bool = False) -> None:
        self.value = bool(value)
        self.redraw()
        if notify and self.command:
            self.command(self.value)

    def _on_click(self, _event):
        self.set(not self.value, notify=True)

    def redraw(self):
        self.delete("all")
        w = max(self.winfo_width(), int(self.cget("width")))
        h = max(self.winfo_height(), int(self.cget("height")))
        rounded_rect(self, 1, 1, w - 2, h - 2, 5, fill=self.theme.panel_alt, outline=self.theme.border)
        led_x = 16
        color = self.theme.status_on if self.value else self.theme.status_off
        self.create_oval(led_x - 4, h / 2 - 4, led_x + 4, h / 2 + 4, fill=color, outline="")
        self.create_text(31, h / 2, text="ON" if self.value else "OFF", anchor="w", fill=self.theme.text, font=self.theme.font_mono)
