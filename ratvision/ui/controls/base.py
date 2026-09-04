from __future__ import annotations

import tkinter as tk

from ratvision.ui.theme import ThemeTokens


class ThemedCanvas(tk.Canvas):
    def __init__(self, master, *, theme: ThemeTokens, **kwargs):
        self.theme = theme
        self._redraw_after_id = None
        self._pending_configure_size: tuple[int, int] | None = None
        self._last_redrawn_size: tuple[int, int] | None = None
        kwargs.setdefault("highlightthickness", 0)
        kwargs.setdefault("bd", 0)
        kwargs.setdefault("background", theme.panel)
        super().__init__(master, **kwargs)
        # Windows can emit a dense stream of WM_SIZE/<Configure> events while the
        # user drags a window edge. Coalesce them to one redraw per idle cycle so
        # custom Canvas controls do not queue dozens of obsolete paint passes.
        self.bind("<Configure>", self._on_configure)

    def _on_configure(self, event) -> None:
        size = (max(0, int(getattr(event, "width", 0))), max(0, int(getattr(event, "height", 0))))
        self._pending_configure_size = size
        if self._redraw_after_id is not None:
            return
        if size == self._last_redrawn_size:
            return
        try:
            self._redraw_after_id = self.after_idle(self._flush_configure_redraw)
        except tk.TclError:
            self._redraw_after_id = None

    def _flush_configure_redraw(self) -> None:
        self._redraw_after_id = None
        size = self._pending_configure_size
        self._pending_configure_size = None
        if size is None or size == self._last_redrawn_size:
            return
        self._last_redrawn_size = size
        self.redraw()

    def set_theme(self, theme: ThemeTokens) -> None:
        self.theme = theme
        self.configure(background=theme.panel)
        self.redraw()

    def redraw(self) -> None:
        raise NotImplementedError


def rounded_rect(canvas: tk.Canvas, x1: int, y1: int, x2: int, y2: int, radius: int, **kwargs):
    radius = max(0, min(radius, (x2 - x1) // 2, (y2 - y1) // 2))
    points = [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1,
    ]
    return canvas.create_polygon(points, smooth=True, splinesteps=16, **kwargs)
