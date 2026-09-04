from __future__ import annotations

from .base import ThemedCanvas


class RatLed(ThemedCanvas):
    def __init__(self, master, *, on: bool, theme, size=22):
        self.on = bool(on)
        super().__init__(master, theme=theme, width=size, height=size)
        self.redraw()

    def set(self, on: bool) -> None:
        self.on = bool(on)
        self.redraw()

    def redraw(self):
        self.delete("all")
        size = min(max(self.winfo_width(), int(self.cget("width"))), max(self.winfo_height(), int(self.cget("height"))))
        c = size / 2
        if self.on:
            self.create_oval(c - 7, c - 7, c + 7, c + 7, fill=self.theme.status_on, outline="", stipple="gray50")
            self.create_oval(c - 4, c - 4, c + 4, c + 4, fill=self.theme.status_on, outline="")
        else:
            self.create_oval(c - 5, c - 5, c + 5, c + 5, fill=self.theme.panel, outline=self.theme.status_off, width=2)
