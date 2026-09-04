from __future__ import annotations

from collections.abc import Callable

from .base import ThemedCanvas


class RatSlider(ThemedCanvas):
    def __init__(self, master, *, value: float, minimum: float, maximum: float, command: Callable[[float], None] | None, theme, width=320, height=34):
        self.minimum = float(minimum)
        self.maximum = float(maximum)
        self.value = self._clamp(float(value))
        self.command = command
        super().__init__(master, theme=theme, width=width, height=height, cursor="hand2", takefocus=1)
        self.bind("<Button-1>", self._on_pointer)
        self.bind("<B1-Motion>", self._on_pointer)
        self.bind("<Left>", self._on_key)
        self.bind("<Right>", self._on_key)
        self.bind("<Home>", self._on_key)
        self.bind("<End>", self._on_key)
        self.redraw()

    def _clamp(self, value: float) -> float:
        return min(max(value, self.minimum), self.maximum)

    def set(self, value: float, *, notify: bool = False) -> None:
        self.value = self._clamp(float(value))
        self.redraw()
        if notify and self.command:
            self.command(self.value)

    def _on_key(self, event):
        step = (self.maximum - self.minimum) / 100.0 if self.maximum != self.minimum else 0.0
        if event.keysym == "Left":
            self.set(self.value - step, notify=True)
        elif event.keysym == "Right":
            self.set(self.value + step, notify=True)
        elif event.keysym == "Home":
            self.set(self.minimum, notify=True)
        elif event.keysym == "End":
            self.set(self.maximum, notify=True)
        return "break"

    def _on_pointer(self, event):
        self.focus_set()
        width = max(self.winfo_width(), int(self.cget("width")))
        start, end = 10, max(11, width - 10)
        ratio = min(max((event.x - start) / (end - start), 0.0), 1.0)
        self.set(self.minimum + ratio * (self.maximum - self.minimum), notify=True)

    def redraw(self):
        self.delete("all")
        width = max(self.winfo_width(), int(self.cget("width")))
        height = max(self.winfo_height(), int(self.cget("height")))
        y = height / 2
        start, end = 10, width - 10
        ratio = 0.0 if self.maximum == self.minimum else (self.value - self.minimum) / (self.maximum - self.minimum)
        thumb = start + ratio * (end - start)
        self.create_line(start, y, end, y, fill=self.theme.track, width=3)
        self.create_line(start, y, thumb, y, fill=self.theme.slider_active, width=3)
        self.create_oval(thumb - 5, y - 5, thumb + 5, y + 5, fill=self.theme.text, outline=self.theme.panel, width=1)
