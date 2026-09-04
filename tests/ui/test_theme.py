import tkinter as tk

from ratvision.domain.models import ThemeMode
from ratvision.ui.theme import ThemeManager


def test_clean_lab_uses_blue_for_selection_not_xrat_green():
    tokens = ThemeManager().tokens(ThemeMode.DAY)
    assert tokens.accent != tokens.status_on
    assert tokens.accent.lower() == "#39aeea"


def test_level_black_has_near_black_background_and_distinct_status_green():
    tokens = ThemeManager().tokens(ThemeMode.NIGHT)
    assert tokens.background.lower() == "#070809"
    assert tokens.status_on.lower() == "#39ff74"
    assert tokens.status_on != tokens.accent


def test_theme_manager_applies_tk_background():
    root = tk.Tk()
    root.withdraw()
    manager = ThemeManager()
    manager.apply(root, ThemeMode.DAY)
    assert root.cget("background").lower() == manager.current.background.lower()
    root.destroy()


def test_follow_windows_resolves_to_current_system_theme():
    manager = ThemeManager(system_theme_resolver=lambda: ThemeMode.DAY)
    tokens = manager.tokens(ThemeMode.SYSTEM)
    assert tokens.mode == ThemeMode.DAY
    assert tokens.accent.lower() == "#39aeea"
