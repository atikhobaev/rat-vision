import tkinter as tk

from ratvision.domain.models import ThemeMode
from ratvision.ui.controls.button import RatButton
from ratvision.ui.controls.card import RatCard
from ratvision.ui.controls.checkbox import RatCheckBox
from ratvision.ui.controls.led import RatLed
from ratvision.ui.controls.slider import RatSlider
from ratvision.ui.controls.toggle import RatToggle
from ratvision.ui.theme import ThemeManager


def test_custom_controls_mount_and_redraw():
    root = tk.Tk()
    root.withdraw()
    theme = ThemeManager().tokens(ThemeMode.NIGHT)
    values = []
    controls = [
        RatButton(root, text="ADD GAME", command=lambda: None, theme=theme),
        RatToggle(root, value=True, command=lambda v: values.append(v), theme=theme),
        RatSlider(root, value=0.5, minimum=0.0, maximum=1.0, command=lambda v: values.append(v), theme=theme),
        RatCheckBox(root, text="DISPLAY 1", checked=True, command=lambda v: values.append(v), theme=theme),
        RatLed(root, on=True, theme=theme),
        RatCard(root, theme=theme),
    ]
    for control in controls:
        control.pack()
        control.update_idletasks()
        assert control.winfo_exists()
    day = ThemeManager().tokens(ThemeMode.DAY)
    for control in controls:
        control.set_theme(day)
        control.update_idletasks()
    root.destroy()


def test_toggle_invokes_command_when_clicked():
    root = tk.Tk()
    root.withdraw()
    seen = []
    toggle = RatToggle(root, value=False, command=seen.append, theme=ThemeManager().tokens(ThemeMode.NIGHT))
    toggle._on_click(None)
    assert seen == [True]
    assert toggle.value is True
    root.destroy()


def test_slider_supports_keyboard_adjustment():
    root = tk.Tk(); root.withdraw()
    theme = ThemeManager().tokens(ThemeMode.NIGHT)
    seen = []
    slider = RatSlider(root, value=0.5, minimum=0.0, maximum=1.0, command=seen.append, theme=theme)
    slider.pack()
    root.update_idletasks()
    slider._on_key(type("E", (), {"keysym": "Right"})())
    assert slider.value > 0.5
    assert seen and seen[-1] == slider.value
    root.destroy()


def test_themed_canvas_coalesces_resize_redraws_until_idle():
    from ratvision.ui.controls.base import ThemedCanvas

    root = tk.Tk(); root.withdraw()
    theme = ThemeManager().tokens(ThemeMode.NIGHT)

    class ProbeCanvas(ThemedCanvas):
        def __init__(self, *args, **kwargs):
            self.redraw_count = 0
            super().__init__(*args, **kwargs)
        def redraw(self):
            self.redraw_count += 1

    canvas = ProbeCanvas(root, theme=theme, width=100, height=40)
    canvas.pack()
    root.update_idletasks()
    before = canvas.redraw_count
    event = type("E", (), {"width": 220, "height": 60})()
    canvas._on_configure(event)
    canvas._on_configure(event)
    canvas._on_configure(event)
    assert canvas.redraw_count == before
    root.update_idletasks()
    assert canvas.redraw_count == before + 1
    root.destroy()
