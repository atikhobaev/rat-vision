import tkinter as tk

from ratvision.domain.models import ThemeMode
from ratvision.ui.theme import ThemeManager
from ratvision.ui.tooltip import attach_tooltip


def test_tooltip_attaches_to_widget_and_can_render_text_immediately():
    root = tk.Tk(); root.withdraw()
    label = tk.Label(root, text="Target")
    label.pack()
    tooltip = attach_tooltip(label, "Helpful explanation", ThemeManager().tokens(ThemeMode.NIGHT), delay_ms=1)

    assert label._rat_tooltip is tooltip
    assert tooltip.text == "Helpful explanation"
    tooltip.show_now()
    assert tooltip.window is not None
    labels = [child for child in tooltip.window.winfo_children() if isinstance(child, tk.Label)]
    assert labels and labels[0].cget("text") == "Helpful explanation"
    tooltip.hide()
    root.destroy()
