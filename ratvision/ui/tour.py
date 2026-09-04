from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Callable
import tkinter as tk

from ratvision.ui.theme import ThemeTokens


@dataclass(frozen=True, slots=True)
class TourStep:
    target: Callable[[], tk.Misc | None]
    title: str
    text: str


class TutorialTour:
    def __init__(self, root: tk.Misc, theme: ThemeTokens, steps: list[TourStep]):
        self.root = root
        self.theme = theme
        self.steps = list(steps)
        self.index = 0
        self.active = False
        self.card: tk.Toplevel | None = None
        self.dim: tk.Toplevel | None = None
        self._borders: list[tk.Toplevel] = []
        self.counter_label: tk.Label | None = None
        self.close_button: tk.Button | None = None
        self.overlay_close: tk.Toplevel | None = None
        self.overlay_close_button: tk.Button | None = None
        self._current_target: tk.Misc | None = None
        self._root_bind_id: str | None = None
        self._reposition_after_id = None
        self._layer_after_id = None
        self._manual_card_offset: tuple[int, int] | None = None
        self._drag_origin: tuple[int, int, int, int] | None = None

    def start(self):
        if not self.steps:
            return
        self.active = True
        self.index = 0
        if self._root_bind_id is None:
            self._root_bind_id = self.root.bind("<Configure>", self._on_root_configure, add="+")
        self._render()

    def next(self):
        if not self.active:
            return
        if self.index >= len(self.steps) - 1:
            self.finish()
            return
        self.index += 1
        self._render()

    def previous(self):
        if not self.active:
            return
        if self.index > 0:
            self.index -= 1
            self._render()

    def finish(self):
        self.active = False
        self._destroy_windows()
        if self._root_bind_id is not None:
            try:
                self.root.unbind("<Configure>", self._root_bind_id)
            except tk.TclError:
                pass
            self._root_bind_id = None
        if self._reposition_after_id is not None:
            try:
                self.root.after_cancel(self._reposition_after_id)
            except tk.TclError:
                pass
            self._reposition_after_id = None
        if self._layer_after_id is not None:
            try:
                self.root.after_cancel(self._layer_after_id)
            except tk.TclError:
                pass
            self._layer_after_id = None
        self._current_target = None
        self._manual_card_offset = None
        self._drag_origin = None

    def _destroy_windows(self):
        for window in self._borders:
            try:
                window.destroy()
            except tk.TclError:
                pass
        self._borders.clear()
        for attr in ("card", "dim", "overlay_close"):
            window = getattr(self, attr)
            if window is not None:
                try:
                    window.destroy()
                except tk.TclError:
                    pass
                setattr(self, attr, None)
        self.counter_label = None
        self.close_button = None
        self.overlay_close_button = None

    def _render(self):
        self._destroy_windows()
        self._manual_card_offset = None
        self._drag_origin = None
        if not self.active or not self.steps:
            return
        try:
            self.root.update_idletasks()
        except tk.TclError:
            self.finish()
            return
        step = self.steps[self.index]
        target = step.target()
        if target is None:
            if self.index < len(self.steps) - 1:
                self.index += 1
                self._render()
            else:
                self.finish()
            return

        self._current_target = target
        self._create_dim()
        self._create_highlight(target)
        self._create_card(target, step)
        self._create_overlay_close()
        # Every native tour window is created withdrawn. Geometry is applied
        # first, then all layers are mapped together. This prevents the first
        # tour frame from flashing at the window manager default position (0,0).
        self._reposition()
        self._show_overlay_windows()
        try:
            # Native alpha/override-redirect windows can change stacking when they
            # become mapped. Reassert the order after the map cycle, never before:
            # lifting an unmapped Toplevel can make some WMs reset it to 0,0.
            self._layer_after_id = self.root.after(20, self._run_scheduled_layer_raise)
        except tk.TclError:
            self._layer_after_id = None

    def _create_dim(self):
        dim = tk.Toplevel(self.root)
        dim.withdraw()
        dim.overrideredirect(True)
        dim.configure(background="#000000")
        alpha_supported = False
        try:
            dim.attributes("-alpha", 0.16)
            dim.attributes("-topmost", True)
            alpha_supported = float(dim.attributes("-alpha")) < 0.95
        except (tk.TclError, TypeError, ValueError):
            alpha_supported = False
        if not alpha_supported:
            dim.destroy()
            self.dim = None
            return
        dim.bind("<Button-1>", self._on_dim_click, add="+")
        self.dim = dim

    def _on_dim_click(self, _event=None):
        """Close the tour when the user clicks the dimmed background."""
        self.finish()

    def _create_overlay_close(self):
        """Create a dedicated close control that belongs to the dim overlay."""
        close = tk.Toplevel(self.root)
        close.withdraw()
        close.overrideredirect(True)
        close.configure(background=self.theme.border)
        try:
            close.attributes("-topmost", True)
        except tk.TclError:
            pass
        button = tk.Button(
            close,
            text="✕",
            command=self.finish,
            bd=0,
            relief="flat",
            background=self.theme.panel_alt,
            foreground=self.theme.text,
            activebackground=self.theme.panel,
            activeforeground=self.theme.text,
            font=self.theme.font_mono,
            cursor="hand2",
            padx=7,
            pady=3,
        )
        button.pack(padx=1, pady=1, fill="both", expand=True)
        self.overlay_close = close
        self.overlay_close_button = button

    def _show_overlay_windows(self):
        """Map already-positioned tour layers without an intermediate 0,0 frame."""
        if not self.active:
            return
        try:
            if self.dim is not None:
                self.dim.deiconify()
            for border in self._borders:
                border.deiconify()
            if self.card is not None:
                self.card.deiconify()
            if self.overlay_close is not None:
                self.overlay_close.deiconify()
        except tk.TclError:
            return

    def _raise_overlay_layers(self):
        """Enforce deterministic native-window stacking for every tour redraw.

        Windows can raise an alpha Toplevel again after a geometry/alpha change.
        Reasserting this order keeps the help card clickable on every step.
        """
        if not self.active:
            return
        anchor = None
        try:
            if self.dim is not None:
                self.dim.lift()
                anchor = self.dim
            for border in self._borders:
                if anchor is None:
                    border.lift()
                else:
                    border.lift(anchor)
                anchor = border
            if self.card is not None:
                if anchor is None:
                    self.card.lift()
                else:
                    self.card.lift(anchor)
                anchor = self.card
            if self.overlay_close is not None:
                if anchor is None:
                    self.overlay_close.lift()
                else:
                    self.overlay_close.lift(anchor)
        except (tk.TclError, AttributeError):
            return

    def _run_scheduled_layer_raise(self):
        self._layer_after_id = None
        if not self.active:
            return
        self._raise_overlay_layers()

    def _line_window(self):
        line = tk.Toplevel(self.root)
        line.withdraw()
        line.overrideredirect(True)
        line.configure(background=self.theme.status_on)
        try:
            line.attributes("-topmost", True)
        except tk.TclError:
            pass
        self._borders.append(line)

    def _create_highlight(self, _target: tk.Misc):
        for _ in range(4):
            self._line_window()

    def _position_highlight(self, target: tk.Misc):
        if len(self._borders) != 4:
            return
        try:
            x = target.winfo_rootx() - 4
            y = target.winfo_rooty() - 4
            w = max(8, target.winfo_width() + 8)
            h = max(8, target.winfo_height() + 8)
        except tk.TclError:
            return
        thickness = 3
        geometries = (
            (x, y, w, thickness),
            (x, y + h - thickness, w, thickness),
            (x, y, thickness, h),
            (x + w - thickness, y, thickness, h),
        )
        for window, (gx, gy, gw, gh) in zip(self._borders, geometries):
            window.geometry(f"{max(1, gw)}x{max(1, gh)}+{gx}+{gy}")

    def _create_card(self, target: tk.Misc, step: TourStep):
        card = tk.Toplevel(self.root)
        card.withdraw()
        card.overrideredirect(True)
        card.configure(background=self.theme.border)
        try:
            card.attributes("-topmost", True)
        except tk.TclError:
            pass
        panel = tk.Frame(card, background=self.theme.panel)
        panel.pack(padx=1, pady=1, fill="both", expand=True)

        header = tk.Frame(panel, background=self.theme.panel, cursor="fleur")
        header.pack(fill="x", padx=12, pady=(10, 2))
        self.counter_label = tk.Label(
            header,
            text=f"{self.index + 1:02d} / {len(self.steps):02d}",
            background=self.theme.panel,
            foreground=self.theme.text_muted,
            font=self.theme.font_mono,
            cursor="fleur",
        )
        self.counter_label.pack(side="left")
        self.close_button = tk.Button(
            header,
            text="✕",
            command=self.finish,
            bd=0,
            background=self.theme.panel,
            foreground=self.theme.text_muted,
            activebackground=self.theme.panel_alt,
            activeforeground=self.theme.text,
            font=self.theme.font_mono,
            cursor="hand2",
            padx=5,
            pady=0,
        )
        self.close_button.pack(side="right")
        title = tk.Label(
            panel,
            text=step.title,
            background=self.theme.panel,
            foreground=self.theme.text,
            font=self.theme.font_display,
            anchor="w",
            cursor="fleur",
        )
        title.pack(fill="x", padx=16)
        body = tk.Label(
            panel,
            text=step.text,
            background=self.theme.panel,
            foreground=self.theme.text,
            font=self.theme.font_ui,
            justify="left",
            wraplength=340,
            anchor="w",
        )
        body.pack(fill="x", padx=16, pady=(7, 12))
        actions = tk.Frame(panel, background=self.theme.panel)
        actions.pack(fill="x", padx=12, pady=(0, 12))
        skip = tk.Button(actions, text="SKIP", command=self.finish, bd=0, background=self.theme.panel, foreground=self.theme.text_muted, activebackground=self.theme.panel_alt, activeforeground=self.theme.text, font=self.theme.font_mono)
        skip.pack(side="left")
        if self.index > 0:
            tk.Button(actions, text="← BACK", command=self.previous, bd=0, background=self.theme.panel, foreground=self.theme.text, activebackground=self.theme.panel_alt, activeforeground=self.theme.text, font=self.theme.font_mono).pack(side="right", padx=(8, 0))
        next_text = "FINISH" if self.index == len(self.steps) - 1 else "NEXT →"
        tk.Button(actions, text=next_text, command=self.next, bd=0, background=self.theme.accent_soft, foreground=self.theme.text, activebackground=self.theme.accent_soft, activeforeground=self.theme.text, font=self.theme.font_mono).pack(side="right", padx=(8, 0), ipadx=8, ipady=4)

        for draggable in (header, self.counter_label, title):
            draggable.bind("<ButtonPress-1>", self._drag_start, add="+")
            draggable.bind("<B1-Motion>", self._drag_move, add="+")

        card.update_idletasks()
        self.card = card
        self._position_card(target)

    def _auto_card_position(self, target: tk.Misc) -> tuple[int, int]:
        if self.card is None:
            return (0, 0)
        cw, ch = self.card.winfo_reqwidth(), self.card.winfo_reqheight()
        tx, ty = target.winfo_rootx(), target.winfo_rooty()
        tw = target.winfo_width()
        screen_w, screen_h = target.winfo_screenwidth(), target.winfo_screenheight()
        x = tx + tw + 16
        y = ty
        if x + cw > screen_w - 12:
            x = max(12, tx - cw - 16)
        if y + ch > screen_h - 12:
            y = max(12, screen_h - ch - 12)
        return x, y

    def _position_card(self, target: tk.Misc):
        if self.card is None:
            return
        if self._manual_card_offset is None:
            x, y = self._auto_card_position(target)
        else:
            root_x, root_y = self.root.winfo_rootx(), self.root.winfo_rooty()
            x = root_x + self._manual_card_offset[0]
            y = root_y + self._manual_card_offset[1]
        self.card.geometry(f"+{x}+{y}")

    def _on_root_configure(self, _event=None):
        if not self.active:
            return
        if self._reposition_after_id is not None:
            return
        try:
            self._reposition_after_id = self.root.after_idle(self._run_scheduled_reposition)
        except tk.TclError:
            self._reposition_after_id = None

    def _run_scheduled_reposition(self):
        self._reposition_after_id = None
        self._reposition()
        if self.active and self._layer_after_id is None:
            try:
                self._layer_after_id = self.root.after(20, self._run_scheduled_layer_raise)
            except tk.TclError:
                self._layer_after_id = None

    def _reposition(self):
        if not self.active or self._current_target is None:
            return
        try:
            self.root.update_idletasks()
            if self.dim is not None:
                x, y = self.root.winfo_rootx(), self.root.winfo_rooty()
                w, h = max(1, self.root.winfo_width()), max(1, self.root.winfo_height())
                self.dim.geometry(f"{w}x{h}+{x}+{y}")
            self._position_highlight(self._current_target)
            self._position_card(self._current_target)
            if self.overlay_close is not None:
                if self.dim is not None:
                    ox, oy = x + w - 46, y + 12
                else:
                    ox = self.root.winfo_rootx() + self.root.winfo_width() - 46
                    oy = self.root.winfo_rooty() + 12
                self.overlay_close.geometry(f"34x30+{ox}+{oy}")
        except tk.TclError:
            return

    def _drag_start(self, event):
        if self.card is None:
            return
        self._drag_origin = (
            int(event.x_root),
            int(event.y_root),
            self.card.winfo_x(),
            self.card.winfo_y(),
        )

    def _drag_move(self, event):
        if self.card is None or self._drag_origin is None:
            return
        start_x, start_y, card_x, card_y = self._drag_origin
        x = card_x + int(event.x_root) - start_x
        y = card_y + int(event.y_root) - start_y
        self.card.geometry(f"+{x}+{y}")
        root_x, root_y = self.root.winfo_rootx(), self.root.winfo_rooty()
        self._manual_card_offset = (x - root_x, y - root_y)
