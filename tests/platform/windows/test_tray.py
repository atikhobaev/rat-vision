from ratvision import __version__
from ratvision.platform.windows.tray import TrayActions, WindowsTrayBackend
from ratvision.ui.tray_assets import render_tray_icon


class FakeShell:
    def __init__(self):
        self.added = []
        self.updated = []
        self.removed = 0

    def add(self, icon, tooltip, menu_items, *, default_action=None):
        self.default_action = default_action
        self.added.append((icon, tooltip, list(menu_items)))

    def update(self, icon, tooltip):
        self.updated.append((icon, tooltip))

    def remove(self):
        self.removed += 1


def dummy_actions():
    return TrayActions(
        open_app=lambda: None,
        toggle_enabled=lambda: None,
        open_settings=lambda: None,
        donate=lambda: None,
        exit_app=lambda: None,
    )


def test_tray_renderer_has_green_lamp_only_in_on_state():
    off = render_tray_icon(False, size=32)
    on = render_tray_icon(True, size=32)
    off_pixel = off.getpixel((26, 26))
    on_pixel = on.getpixel((26, 26))
    assert on_pixel[1] > on_pixel[0] and on_pixel[1] > 150
    assert off_pixel[1] < 150


def test_windows_tray_backend_has_exactly_two_global_icon_states():
    shell = FakeShell()
    backend = WindowsTrayBackend(shell=shell)
    backend.start(dummy_actions())
    backend.set_enabled(False)
    backend.set_enabled(True)
    assert len(shell.updated) == 2
    assert shell.updated[0][1].endswith("DISABLED")
    assert shell.updated[1][1].endswith("ENABLED")
    assert shell.updated[0][0].tobytes() != shell.updated[1][0].tobytes()
    backend.stop()
    assert shell.removed == 1


def test_tray_menu_contains_required_actions_and_no_profile_active_state():
    shell = FakeShell()
    backend = WindowsTrayBackend(shell=shell)
    backend.start(dummy_actions())
    labels = [item.label for item in shell.added[0][2]]
    assert labels == [
        f"RAT VISION v{__version__}",
        "XRAT TRACING",
        "Open RAT VISION",
        "Settings",
        "Buy me a coffee",
        "Exit",
    ]
    assert "Profile active" not in labels


def test_left_click_on_native_tray_dispatches_default_open_action():
    from ratvision.platform.windows.tray import WM_LBUTTONUP, _Win32TrayShell

    calls = []
    shell = object.__new__(_Win32TrayShell)
    shell._default_action = lambda: calls.append("open")
    shell._show_menu = lambda: calls.append("menu")

    handled = shell._dispatch_notification(WM_LBUTTONUP)

    assert handled is True
    assert calls == ["open"]


def test_windows_tray_backend_wires_left_click_to_open_action():
    shell = FakeShell()
    calls = []
    actions = TrayActions(
        open_app=lambda: calls.append("open"),
        toggle_enabled=lambda: None,
        open_settings=lambda: None,
        donate=lambda: None,
        exit_app=lambda: None,
    )
    backend = WindowsTrayBackend(shell=shell)
    backend.start(actions)

    assert shell.default_action is not None
    shell.default_action()
    assert calls == ["open"]


def test_tray_renderer_uses_approved_nvg_rat_brand_in_both_states():
    for enabled in (False, True):
        image = render_tray_icon(enabled, size=48).convert("RGBA")
        green = sum(
            1 for r, g, b, a in image.get_flattened_data()
            if a > 128 and g > 150 and g > r * 1.3 and g > b * 1.3
        )
        bright = sum(1 for r, g, b, a in image.get_flattened_data() if a > 128 and r > 200 and g > 200 and b > 200)
        assert green > 4
        assert bright > 15


def test_small_tray_icon_uses_dedicated_high_coverage_glyph():
    image = render_tray_icon(False, size=16).convert("RGBA")
    foreground = sum(
        1 for r, g, b, a in image.get_flattened_data()
        if a > 128 and ((r > 175 and g > 175 and b > 175) or (g > 115 and g > r * 1.2 and g > b * 1.2))
    )
    assert foreground >= 42


def test_public_beta_tray_icon_is_extra_large_at_16px():
    image = render_tray_icon(False, size=16).convert('RGBA')
    foreground = sum(
        1 for r, g, b, a in image.get_flattened_data()
        if a > 128 and ((r > 175 and g > 175 and b > 175) or (g > 115 and g > r * 1.2 and g > b * 1.2))
    )
    assert foreground >= 105
