from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
import tkinter as tk

from ratvision.controller import AppController
from ratvision.domain.models import DisplayInfo, ThemeMode
from ratvision.persistence.settings_store import SettingsStore
from ratvision.runtime_faults import install_fault_logging
from ratvision.platform.simulation import (
    SimulationColorBackend,
    SimulationDisplayProvider,
    SimulationForegroundProvider,
    SimulationStartupBackend,
    SimulationTrayBackend,
)
from ratvision.ui.main_window import MainWindow


def _simulation_displays() -> list[DisplayInfo]:
    return [
        DisplayInfo("SIM-DISPLAY1", "DISPLAY 1", 2560, 1440, 165.0, True, True),
        DisplayInfo("SIM-DISPLAY2", "DISPLAY 2", 1920, 1080, 60.0, False, True),
    ]


def _default_settings_path() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home()))
        return base / "RAT VISION" / "settings.json"
    return Path.home() / ".config" / "ratvision" / "settings.json"


def create_simulation_app(
    *,
    settings_path: Path,
    theme_override: ThemeMode | None = None,
):
    root = tk.Tk()
    displays = _simulation_displays()
    controller = AppController(
        root=root,
        settings_store=SettingsStore(Path(settings_path)),
        display_provider=SimulationDisplayProvider(displays),
        foreground_provider=SimulationForegroundProvider(),
        color_backend=SimulationColorBackend(),
        tray_backend=SimulationTrayBackend(),
        startup_backend=SimulationStartupBackend(),
        platform_name="simulation",
    )
    if theme_override is not None:
        controller.set_theme(theme_override)
    window = MainWindow(root, controller)
    controller.attach_main_window(window)
    root.protocol("WM_DELETE_WINDOW", controller.shutdown)
    controller.start_services()
    if controller.settings.start_minimized:
        root.withdraw()
    return root, controller, window


def create_windows_app(
    *,
    settings_path: Path,
    theme_override: ThemeMode | None = None,
):
    if sys.platform != "win32":
        raise RuntimeError("RAT VISION production mode requires Windows; use --simulate here")

    from ratvision.platform.windows.color_backend import WindowsColorBackend
    from ratvision.platform.windows.displays import WindowsDisplayProvider
    from ratvision.platform.windows.foreground import WindowsForegroundProvider
    from ratvision.platform.windows.startup import WindowsStartupBackend
    from ratvision.platform.windows.tray import WindowsTrayBackend

    root = tk.Tk()
    install_fault_logging(root, Path(settings_path).parent / "logs" / "crash.log")
    if getattr(sys, "frozen", False):
        startup_command = f'"{sys.executable}"'
    else:
        startup_command = f'"{sys.executable}" -m ratvision'
    controller = AppController(
        root=root,
        settings_store=SettingsStore(Path(settings_path)),
        display_provider=WindowsDisplayProvider(),
        foreground_provider=WindowsForegroundProvider(),
        color_backend=WindowsColorBackend(),
        tray_backend=WindowsTrayBackend(),
        startup_backend=WindowsStartupBackend(command=startup_command),
        platform_name="windows",
    )
    if theme_override is not None:
        controller.set_theme(theme_override)
    window = MainWindow(root, controller)
    controller.attach_main_window(window)

    def close_requested():
        if controller.settings.close_to_tray:
            root.withdraw()
        else:
            controller.shutdown()

    root.protocol("WM_DELETE_WINDOW", close_requested)
    controller.start_services()
    if controller.settings.start_minimized:
        root.withdraw()
    return root, controller, window


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ratvision", description="RAT VISION game display profiles")
    parser.add_argument("--simulate", action="store_true", help="use Linux/Windows simulation backends")
    parser.add_argument("--settings", type=Path, default=None, help="path to settings.json")
    parser.add_argument(
        "--theme",
        choices=[mode.value for mode in ThemeMode],
        default=None,
        help="override startup theme",
    )
    return parser



def run_dvc_helper_cli(argv: list[str]) -> int:
    from ratvision.platform.windows.dvc_helper import main as dvc_helper_main
    return int(dvc_helper_main(argv))

def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "--dvc-helper":
        return run_dvc_helper_cli(argv[1:])
    args = build_parser().parse_args(argv)
    settings_path = args.settings or _default_settings_path()
    theme = ThemeMode(args.theme) if args.theme else None
    if args.simulate:
        root, controller, _window = create_simulation_app(settings_path=settings_path, theme_override=theme)
    else:
        root, controller, _window = create_windows_app(settings_path=settings_path, theme_override=theme)
    try:
        root.mainloop()
    finally:
        if not getattr(controller, "_shutdown", False):
            controller.shutdown()
    return 0
