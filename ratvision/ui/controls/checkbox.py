from __future__ import annotations

from collections.abc import Callable

from .base import ThemedCanvas, rounded_rect


class RatCheckBox(ThemedCanvas):
    def __init__(self, master, *, text: str, checked: bool, command: Callable[[bool], None] | None, theme, width=280, height=38):
        self.text = text
        self.checked = bool(checked)
        self.command = command
        super().__init__(master, theme=theme, width=width, height=height, cursor="hand2")
        self.bind("<Button-1>", self._on_click)
        self.redraw()

    def set(self, value: bool, *, notify: bool = False) -> None:
        self.checked = bool(value)
        self.redraw()
        if notify and self.command:
            self.command(self.checked)

    def _on_click(self, _event):
        self.set(not self.checked, notify=True)

    def redraw(self):
        self.delete("all")
        h = max(self.winfo_height(), int(self.cget("height")))
        box_y = h / 2 - 7
        fill = self.theme.accent if self.checked else self.theme.panel
        rounded_rect(self, 3, int(box_y), 17, int(box_y + 14), 2, fill=fill, outline=self.theme.border)
        if self.checked:
            tick = self.theme.background if self.theme.mode.value == "night" else "#FFFFFF"
            self.create_line(6, h / 2, 9, h / 2 + 3, 15, h / 2 - 5, fill=tick, width=2)
        self.create_text(28, h / 2, text=self.text, anchor="w", fill=self.theme.text, font=self.theme.font_ui)
