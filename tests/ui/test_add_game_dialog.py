import tkinter as tk

from ratvision.domain.models import AppSettings, DisplayInfo, GameProfile, VisualParameters
from ratvision.domain.profile_service import ProfileService
from ratvision.ui.add_game_dialog import AddGameDialog
from ratvision.ui.theme import ThemeManager


class Controller:
    def __init__(self):
        self.displays = [DisplayInfo("D1", "Main", 2560, 1440, 165.0, True, True)]
        self.settings = AppSettings(
            profiles=[
                GameProfile(id="source", name="Source", visual=VisualParameters(0.7, 0.4, 1.4, 68), processes=["source.exe"], display_ids=["D1"])
            ]
        )
        self.profile_service = ProfileService(self.settings)
        self.theme_manager = ThemeManager()
        self.saved = 0
        self.created = None

    def save_settings(self):
        self.saved += 1

    def on_profile_created(self, profile):
        self.created = profile


def test_create_profile_from_exe_defaults_to_primary_display():
    root = tk.Tk(); root.withdraw()
    controller = Controller()
    dialog = AddGameDialog(root, controller, build_ui=False)
    profile = dialog.create_profile(name="My Game", emoji="🎮", processes=[r"C:\\Games\\MYGAME.EXE"])
    assert profile.name == "My Game"
    assert profile.processes == ["mygame.exe"]
    assert profile.display_ids == ["D1"]
    assert profile.visual == VisualParameters()
    assert controller.saved == 1
    root.destroy()


def test_create_profile_can_copy_visuals_without_copying_identity():
    root = tk.Tk(); root.withdraw()
    controller = Controller()
    dialog = AddGameDialog(root, controller, build_ui=False)
    profile = dialog.create_profile(
        name="New Game",
        emoji="🤠",
        processes=["newgame.exe"],
        copy_from_id="source",
    )
    assert profile.visual == controller.profile_service.get("source").visual
    assert profile.processes == ["newgame.exe"]
    assert profile.name == "New Game"
    assert profile.id != "source"
    root.destroy()


def test_profile_step_exposes_monitor_checkboxes_with_primary_selected():
    root = tk.Tk(); root.withdraw()
    controller = Controller()
    controller.displays.append(DisplayInfo("D2", "Second", 1920, 1080, 60.0, False, True))
    dialog = AddGameDialog(root, controller, build_ui=False)
    dialog._source_processes = ["game.exe"]
    dialog._source_name = "Game"
    dialog._build_profile_step()
    assert set(dialog.display_controls) == {"D1", "D2"}
    assert dialog.display_controls["D1"].checked is True
    assert dialog.display_controls["D2"].checked is False
    dialog.window.destroy()
    root.destroy()


def test_profile_step_copy_source_menu_uses_profile_names_not_internal_ids():
    root = tk.Tk(); root.withdraw()
    controller = Controller()
    dialog = AddGameDialog(root, controller, build_ui=False)
    dialog._source_processes = ["game.exe"]
    dialog._source_name = "Game"
    dialog._build_profile_step()
    menu = dialog.starting_menu["menu"]
    assert menu.entrycget(0, "label") == "Default"
    assert "Source" in menu.entrycget(1, "label")
    assert "source" != menu.entrycget(1, "label")
    dialog.window.destroy()
    root.destroy()
