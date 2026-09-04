from ratvision import __version__
import tkinter as tk

from ratvision.domain.models import AppSettings, DisplayInfo, ThemeMode
from ratvision.release_config import ReleaseConfig
from ratvision.ui.settings_view import SettingsView
from ratvision.ui.theme import ThemeManager
from ratvision.updates.service import UpdateService, UpdateStatus


class Controller:
    def __init__(self):
        self.settings = AppSettings(theme=ThemeMode.NIGHT)
        self.displays = [DisplayInfo("D1", "Main", 1920, 1080, 60.0, True, True)]
        self.theme_manager = ThemeManager()
        self.saved = 0
        self.theme_changes = []
        self.update_service = UpdateService(ReleaseConfig('OWNER/rat-vision'))

    def save_settings(self):
        self.saved += 1

    def set_theme(self, mode):
        self.settings.theme = mode
        self.theme_manager.current = self.theme_manager.tokens(mode)
        self.theme_changes.append(mode)

    def export_profiles(self): pass
    def import_profiles(self): pass
    def restore_default_profiles(self): pass
    def copy_diagnostics(self): pass
    def open_logs(self): pass


def test_update_service_reports_unconfigured_repository():
    status = UpdateService(ReleaseConfig('OWNER/rat-vision')).check()
    assert status.status is UpdateStatus.UNCONFIGURED
    assert "GitHub repository" in status.message


def test_settings_view_contains_about_version_and_update_copy():
    root = tk.Tk(); root.withdraw()
    controller = Controller()
    messages = []
    view = SettingsView(root, controller, info_sink=lambda title, msg: messages.append((title, msg)))
    assert f"v{__version__}" in view.about_version_label.cget("text")
    about_text = " ".join(child.cget("text") for child in view.winfo_children() if hasattr(child, "cget") and "text" in child.keys()).lower()
    assert "tarkov-settings" not in about_text
    assert "incheon-kim" not in about_text
    view._check_updates()
    assert messages and "GitHub repository" in messages[0][1]
    root.destroy()


def test_settings_theme_choice_calls_controller_and_autosaves():
    root = tk.Tk(); root.withdraw()
    controller = Controller()
    view = SettingsView(root, controller, info_sink=lambda *_: None)
    view._set_theme("day")
    assert controller.settings.theme is ThemeMode.DAY
    assert controller.theme_changes == [ThemeMode.DAY]
    assert controller.saved == 1
    root.destroy()


def test_settings_interactive_controls_have_explanatory_tooltips():
    root = tk.Tk(); root.withdraw()
    controller = Controller()
    view = SettingsView(root, controller, info_sink=lambda *_: None)
    assert view.controls["launch_with_windows"]._rat_tooltip.text
    assert view.controls["close_to_tray"]._rat_tooltip.text
    assert view.update_button._rat_tooltip.text
    root.destroy()


def test_settings_only_exposes_working_behavior_toggles():
    root = tk.Tk(); root.withdraw()
    controller = Controller()
    view = SettingsView(root, controller, info_sink=lambda *_: None)
    assert set(view.controls) == {
        "launch_with_windows",
        "start_minimized",
        "close_to_tray",
    }
    root.destroy()


def test_analytics_toggle_is_not_shown_when_build_is_unconfigured():
    root=tk.Tk(); root.withdraw()
    controller=Controller()
    view=SettingsView(root,controller,info_sink=lambda *_:None)
    assert 'analytics_enabled' not in view.controls
    root.destroy()


def test_analytics_toggle_is_visible_and_on_in_configured_build():
    class Analytics:
        configured=True
    root=tk.Tk(); root.withdraw()
    controller=Controller(); controller.analytics_service=Analytics()
    view=SettingsView(root,controller,info_sink=lambda *_:None)
    assert 'analytics_enabled' in view.controls
    assert view.controls['analytics_enabled'].checked is True
    root.destroy()


def test_analytics_callback_sees_previous_consent_before_setting_changes():
    class Analytics:
        configured = True

    root=tk.Tk(); root.withdraw()
    controller=Controller(); controller.analytics_service=Analytics()
    observed=[]
    controller.setting_changed=lambda attr, value: observed.append((attr, value, controller.settings.analytics_enabled))
    view=SettingsView(root,controller,info_sink=lambda *_:None)
    view._set_bool('analytics_enabled', False)
    assert observed == [('analytics_enabled', False, True)]
    assert controller.settings.analytics_enabled is False
    root.destroy()
