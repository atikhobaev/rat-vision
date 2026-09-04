from ratvision import __version__
import tkinter as tk

from ratvision.domain.defaults import create_default_profiles
from ratvision.domain.models import AppSettings, DisplayInfo, ThemeMode
from ratvision.domain.profile_service import ProfileService
from ratvision.ui.main_window import MainWindow
from ratvision.ui.theme import ThemeManager


class FakeController:
    def __init__(self):
        self.displays = [
            DisplayInfo("DISPLAY1", "Main display", 2560, 1440, 165.0, True, True),
            DisplayInfo("DISPLAY2", "Second display", 1920, 1080, 60.0, False, True),
        ]
        self.settings = AppSettings(profiles=create_default_profiles(self.displays))
        self.profile_service = ProfileService(self.settings)
        self.theme_manager = ThemeManager()
        self.saved = 0
        self.donated = 0
        self.settings_opened = 0
        self.add_game_opened = 0

    def save_settings(self):
        self.saved += 1

    def set_global_enabled(self, value):
        self.settings.global_enabled = value
        self.saved += 1

    def set_profile_enabled(self, profile_id, value):
        profile = self.profile_service.get(profile_id)
        profile.enabled = bool(value)
        self.saved += 1
        self.last_refreshed = profile_id

    def set_theme(self, mode):
        self.settings.theme = mode
        self.theme_manager.current = self.theme_manager.tokens(mode)

    def refresh_profile(self, profile_id):
        self.last_refreshed = profile_id

    def donate(self):
        self.donated += 1

    def show_settings(self):
        self.settings_opened += 1

    def show_add_game(self):
        self.add_game_opened += 1


def test_main_window_builds_approved_master_detail_structure():
    root = tk.Tk()
    root.withdraw()
    controller = FakeController()
    window = MainWindow(root, controller)
    root.update_idletasks()

    assert root.title() == f"RAT VISION v{__version__}"
    assert len(window.sidebar.profile_rows) == 4
    assert window.sidebar.profile_rows[0].profile.builtin_id == "global"
    assert window.sidebar.donate_button.text == "☕ Buy me a coffee"
    assert window.sidebar.settings_button.text == "⚙ SETTINGS"
    assert set(window.workspace.parameter_sliders) == {"brightness", "contrast", "gamma", "saturation"}
    assert len(window.workspace.display_checks) == 2
    window.select_profile(controller.settings.profiles[1].id)
    assert window.workspace.process_rows[0].executable == "escapefromtarkov.exe"
    assert window.global_toggle.value is True
    root.destroy()


def test_profile_selection_updates_workspace():
    root = tk.Tk()
    root.withdraw()
    controller = FakeController()
    window = MainWindow(root, controller)
    second = controller.settings.profiles[1]
    window.select_profile(second.id)
    assert window.workspace.profile.id == second.id
    assert window.selected_profile_id == second.id
    root.destroy()


def test_slider_change_updates_profile_and_autosaves():
    root = tk.Tk()
    root.withdraw()
    controller = FakeController()
    window = MainWindow(root, controller)
    window.workspace._set_parameter("brightness", 0.73)
    assert window.workspace.profile.visual.brightness == 0.73
    assert controller.saved == 1
    assert controller.last_refreshed == window.workspace.profile.id
    root.destroy()


def test_theme_shortcut_toggles_day_and_night():
    root = tk.Tk()
    root.withdraw()
    controller = FakeController()
    window = MainWindow(root, controller)
    assert controller.settings.theme == ThemeMode.NIGHT
    window.toggle_theme()
    assert controller.settings.theme == ThemeMode.DAY
    window.toggle_theme()
    assert controller.settings.theme == ThemeMode.NIGHT
    root.destroy()


def test_game_profile_rows_use_packaged_semantic_images_and_global_uses_globe_glyph():
    root = tk.Tk()
    root.withdraw()
    controller = FakeController()
    window = MainWindow(root, controller)
    root.update_idletasks()
    global_row, *game_rows = window.sidebar.profile_rows
    assert global_row.emoji_label.cget("text") == "🌐"
    assert all(row.emoji_label.cget("image") for row in game_rows)
    root.destroy()


def test_default_profile_workspace_fits_initial_window_without_vertical_scroll():
    root = tk.Tk()
    controller = FakeController()
    window = MainWindow(root, controller)
    root.update_idletasks()
    root.update()
    viewport_height = window.workspace_canvas.winfo_height()
    assert viewport_height > 1
    assert window.workspace.winfo_reqheight() <= viewport_height - 40
    root.destroy()


def test_header_uses_rat_vision_brand_mark():
    root = tk.Tk()
    root.withdraw()
    controller = FakeController()
    window = MainWindow(root, controller)
    root.update_idletasks()
    assert window.brand_label.cget("image")
    root.destroy()


def test_top_theme_shortcut_autosaves_theme_choice():
    root = tk.Tk()
    root.withdraw()
    controller = FakeController()
    window = MainWindow(root, controller)
    assert controller.saved == 0
    window.toggle_theme()
    assert controller.saved == 1
    root.destroy()


def test_clean_lab_header_keeps_approved_nvg_brand_colors():
    root = tk.Tk()
    root.withdraw()
    controller = FakeController()
    controller.settings.theme = ThemeMode.DAY
    window = MainWindow(root, controller)
    root.update_idletasks()

    image_name = window.brand_label.cget("image")
    green_pixels = 0
    width = int(root.tk.call("image", "width", image_name))
    height = int(root.tk.call("image", "height", image_name))
    for y in range(height):
        for x in range(width):
            if bool(int(root.tk.call(image_name, "transparency", "get", x, y))):
                continue
            r, g, b = map(int, root.tk.call(image_name, "get", x, y))
            if g > 140 and g > r * 1.2 and g > b * 1.2:
                green_pixels += 1

    assert green_pixels > 3
    root.destroy()


def test_mouse_wheel_scrolls_workspace_when_pointer_is_over_workspace():
    root = tk.Tk()
    controller = FakeController()
    window = MainWindow(root, controller)
    root.update_idletasks()
    root.update()
    window.workspace_canvas.create_rectangle(0, 0, 1000, 3000, outline="")
    window._sync_scrollregion()
    window.workspace_canvas.yview_moveto(0.0)
    before = window.workspace_canvas.yview()[0]

    window.workspace.runtime_status.event_generate("<MouseWheel>", delta=-120)
    root.update()
    after = window.workspace_canvas.yview()[0]

    assert after > before
    root.destroy()


def test_copy_settings_refreshes_visible_profile_editor_immediately():
    from ratvision.ui.profile_tools import CopySettingsDialog
    from ratvision.domain.models import VisualParameters

    root = tk.Tk()
    root.withdraw()
    controller = FakeController()
    controller.main_window = None

    def reload_profile_editor(profile_id):
        controller.reloaded_profile_id = profile_id
        controller.main_window.select_profile(profile_id)

    controller.reload_profile_editor = reload_profile_editor
    window = MainWindow(root, controller)
    controller.main_window = window
    target = controller.settings.profiles[0]
    source = controller.settings.profiles[1]
    source.visual = VisualParameters(0.81, 0.32, 1.72, 77)
    assert window.workspace.parameter_sliders["brightness"].value != 0.81

    dialog = CopySettingsDialog.__new__(CopySettingsDialog)
    dialog.controller = controller
    dialog.target_profile_id = target.id
    dialog.window = type("Window", (), {"destroy": lambda self: None})()
    dialog._copy(source.id)

    assert controller.reloaded_profile_id == target.id
    assert window.workspace.parameter_sliders["brightness"].value == 0.81
    assert window.workspace.parameter_sliders["contrast"].value == 0.32
    assert window.workspace.parameter_sliders["gamma"].value == 1.72
    assert window.workspace.parameter_sliders["saturation"].value == 77
    root.destroy()


def test_last_target_process_can_be_removed_and_editor_updates_immediately():
    root = tk.Tk()
    root.withdraw()
    controller = FakeController()
    controller.main_window = None

    def reload_profile_editor(profile_id):
        controller.reloaded_profile_id = profile_id
        controller.main_window.select_profile(profile_id)

    controller.reload_profile_editor = reload_profile_editor
    window = MainWindow(root, controller)
    controller.main_window = window
    specific = next(profile for profile in controller.settings.profiles if profile.builtin_id != "global")
    window.select_profile(specific.id)
    profile = window.workspace.profile
    executable = profile.processes[0]
    assert len(profile.processes) == 1

    window.workspace._remove_process(executable)

    assert profile.processes == []
    assert controller.reloaded_profile_id == profile.id
    assert window.workspace.process_rows == []
    root.destroy()


def test_sidebar_has_fast_toggle_for_every_profile_without_selecting_it():
    root = tk.Tk(); root.withdraw()
    controller = FakeController()
    window = MainWindow(root, controller)
    selected_before = window.selected_profile_id
    row = window.sidebar.profile_rows[1]
    profile = row.profile
    assert profile.enabled is True

    row.toggle._on_click(None)

    assert profile.enabled is False
    assert controller.last_refreshed == profile.id
    assert window.selected_profile_id == selected_before
    root.destroy()


def test_profile_workspace_does_not_duplicate_profile_on_off_toggle():
    root = tk.Tk(); root.withdraw()
    controller = FakeController()
    window = MainWindow(root, controller)
    assert not hasattr(window.workspace, "profile_toggle")
    root.destroy()


def test_global_profile_is_pinned_first_in_sidebar():
    root = tk.Tk(); root.withdraw()
    controller = FakeController()
    window = MainWindow(root, controller)
    assert window.sidebar.profile_rows[0].profile.builtin_id == "global"
    root.destroy()


def test_decorative_three_stripes_are_tall_not_square():
    root = tk.Tk(); root.withdraw()
    controller = FakeController()
    window = MainWindow(root, controller)
    root.update_idletasks()
    items = window.sidebar.stripe.find_withtag("decorative-stripe")
    assert len(items) == 3
    for item in items:
        x1, y1, x2, y2 = window.sidebar.stripe.coords(item)
        assert (y2 - y1) >= 30
        assert (x2 - x1) <= 10
    root.destroy()


def test_global_profile_workspace_hides_process_and_delete_actions():
    root = tk.Tk(); root.withdraw()
    controller = FakeController()
    window = MainWindow(root, controller)
    assert window.workspace.profile.builtin_id == "global"
    assert "PROCESS INDEPENDENT" in window.workspace.target_summary_label.cget("text")
    assert not hasattr(window.workspace, "add_process_button")
    assert not hasattr(window.workspace, "delete_button")
    root.destroy()


def test_main_window_exposes_tour_button_and_tooltips_for_key_controls():
    root = tk.Tk(); root.withdraw()
    controller = FakeController()
    window = MainWindow(root, controller)
    assert window.tour_button.cget("text") == "❔ TOUR"
    assert window.global_toggle._rat_tooltip.text
    assert window.theme_button._rat_tooltip.text
    assert window.sidebar.add_game_button._rat_tooltip.text
    assert window.workspace.parameter_sliders["brightness"]._rat_tooltip.text
    root.destroy()


def test_start_tour_marks_prompt_seen_and_creates_ten_step_tour():
    root = tk.Tk(); root.geometry("1180x760")
    controller = FakeController()
    controller.settings.tour_prompt_seen = False
    window = MainWindow(root, controller)
    root.update()

    window.start_tour()

    assert controller.settings.tour_prompt_seen is True
    assert window.tour is not None
    assert len(window.tour.steps) == 10
    assert window.tour.active is True
    window.tour.finish()
    root.destroy()


def test_first_run_tour_hint_can_be_dismissed_and_is_persisted():
    root = tk.Tk(); root.withdraw()
    controller = FakeController()
    controller.settings.tour_prompt_seen = False
    window = MainWindow(root, controller)
    assert window.sidebar.tour_hint is not None

    window.dismiss_tour_hint()

    assert controller.settings.tour_prompt_seen is True
    assert window.sidebar.tour_hint is None
    assert controller.saved >= 1
    root.destroy()


def test_sidebar_quick_toggles_leave_enough_width_for_profile_names():
    root = tk.Tk(); root.geometry("1180x760")
    controller = FakeController()
    window = MainWindow(root, controller)
    root.update()
    assert min(row.name_label.winfo_width() for row in window.sidebar.profile_rows) >= 155
    root.destroy()


def test_global_profile_uses_globe_marker_in_sidebar():
    root = tk.Tk(); root.withdraw()
    controller = FakeController()
    window = MainWindow(root, controller)
    global_row = window.sidebar.profile_rows[0]
    assert global_row.emoji_label.cget("text") == "🌐"
    root.destroy()


def test_header_pin_toggle_controls_always_on_top_and_persists():
    root = tk.Tk(); root.geometry("800x600")
    controller = FakeController()
    assert controller.settings.always_on_top is False
    window = MainWindow(root, controller)
    assert window.pin_button.cget("text") == "📌"
    assert bool(root.attributes("-topmost")) is False

    window.toggle_always_on_top()
    root.update_idletasks(); root.update()

    assert controller.settings.always_on_top is True
    assert bool(root.attributes("-topmost")) is True
    assert controller.saved == 1
    assert "above other windows" in window.pin_button._rat_tooltip.text.lower()
    root.destroy()


def test_global_profile_and_killa_easter_egg_have_explanatory_tooltips():
    root = tk.Tk(); root.withdraw()
    controller = FakeController()
    window = MainWindow(root, controller)
    global_row = window.sidebar.profile_rows[0]
    global_tip = global_row.toggle._rat_tooltip.text.lower()
    assert "global" in global_tip
    assert "xrat tracing" in global_tip
    assert "game profile" in global_tip
    stripe_tip = window.sidebar.stripe._rat_tooltip.text.lower()
    assert "killa" in stripe_tip
    assert "rat vision" in stripe_tip
    assert "joke" not in stripe_tip and "easter egg" not in stripe_tip
    root.destroy()


def test_persisted_always_on_top_is_applied_when_window_builds():
    root = tk.Tk(); root.geometry("800x600")
    controller = FakeController()
    controller.settings.always_on_top = True
    MainWindow(root, controller)
    root.update_idletasks(); root.update()
    assert bool(root.attributes("-topmost")) is True
    root.destroy()


def test_window_icon_uses_dedicated_application_icon_not_header_brand_mark():
    root = tk.Tk()
    root.withdraw()
    icon_calls = []
    root.iconphoto = lambda default, image: icon_calls.append((default, image))
    controller = FakeController()
    window = MainWindow(root, controller)

    assert icon_calls
    assert icon_calls[-1][0] is True
    assert icon_calls[-1][1] is window.app_icon_image
    assert window.app_icon_image is not window.brand_image
    root.destroy()


def test_killa_stripes_tooltip_keeps_reference_dry_without_explaining_the_joke():
    root = tk.Tk(); root.withdraw()
    controller = FakeController()
    window = MainWindow(root, controller)
    text = window.sidebar.stripe._rat_tooltip.text
    assert "KILLA // ★★★★★" in text
    assert "RAT VISION" in text
    lowered = text.lower()
    assert "joke" not in lowered
    assert "easter" not in lowered
    assert "шут" not in lowered
    assert "пасх" not in lowered
    root.destroy()
