from __future__ import annotations

import tkinter as tk

from ratvision.ui.theme import ThemeTokens


class RatTooltip:
    def __init__(self, widget: tk.Misc, text: str, theme: ThemeTokens, *, delay_ms: int = 475):
        self.widget = widget
        self.text = text
        self.theme = theme
        self.delay_ms = int(delay_ms)
        self.window: tk.Toplevel | None = None
        self._after_id = None
        widget.bind("<Enter>", self._on_enter, add="+")
        widget.bind("<Leave>", self._on_leave, add="+")
        widget.bind("<ButtonPress>", self._on_leave, add="+")
        widget.bind("<Destroy>", self._on_destroy, add="+")

    def _on_enter(self, _event=None):
        self._cancel_pending()
        try:
            self._after_id = self.widget.after(self.delay_ms, self.show_now)
        except tk.TclError:
            self._after_id = None

    def _on_leave(self, _event=None):
        self._cancel_pending()
        self.hide()

    def _on_destroy(self, _event=None):
        self._after_id = None
        self.hide()

    def _cancel_pending(self):
        if self._after_id is None:
            return
        try:
            self.widget.after_cancel(self._after_id)
        except tk.TclError:
            pass
        self._after_id = None

    def show_now(self):
        self._after_id = None
        if self.window is not None:
            return
        try:
            if not self.widget.winfo_exists():
                return
            top = tk.Toplevel(self.widget)
            top.overrideredirect(True)
            try:
                top.attributes("-topmost", True)
            except tk.TclError:
                pass
            top.configure(background=self.theme.border)
            label = tk.Label(
                top,
                text=self.text,
                justify="left",
                wraplength=330,
                background=self.theme.panel,
                foreground=self.theme.text,
                font=self.theme.font_small,
                padx=10,
                pady=7,
            )
            label.pack(padx=1, pady=1)
            top.update_idletasks()
            x = self.widget.winfo_rootx() + min(max(self.widget.winfo_width() // 2, 8), 120)
            y = self.widget.winfo_rooty() + self.widget.winfo_height() + 8
            screen_w = max(1, self.widget.winfo_screenwidth())
            screen_h = max(1, self.widget.winfo_screenheight())
            width = top.winfo_reqwidth()
            height = top.winfo_reqheight()
            x = min(max(4, x), max(4, screen_w - width - 8))
            if y + height > screen_h - 8:
                y = max(4, self.widget.winfo_rooty() - height - 8)
            top.geometry(f"+{x}+{y}")
            self.window = top
        except tk.TclError:
            self.window = None

    def hide(self):
        if self.window is None:
            return
        try:
            self.window.destroy()
        except tk.TclError:
            pass
        self.window = None


def attach_tooltip(widget: tk.Misc, text: str, theme: ThemeTokens, *, delay_ms: int = 475) -> RatTooltip:
    tooltip = RatTooltip(widget, text, theme, delay_ms=delay_ms)
    setattr(widget, "_rat_tooltip", tooltip)
    return tooltip
