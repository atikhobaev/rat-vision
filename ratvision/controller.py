from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import sys
import webbrowser
import queue
import threading
import platform
from collections.abc import Callable

from ratvision import __version__
from ratvision.diagnostics.collector import DiagnosticsCollector
from ratvision.domain.activation_coordinator import ActivationCoordinator
from ratvision.domain.defaults import create_default_profiles
from ratvision.domain.models import ForegroundProcess, GameProfile, ThemeMode
from ratvision.domain.profile_service import ProfileService
from ratvision.ui.theme import ThemeManager
from ratvision.updates.service import UpdateService
from ratvision.analytics.service import AnalyticsService
from ratvision.updates.edition import detect_edition


DONATION_URL = "https://dalink.to/bazaz"


@dataclass(frozen=True, slots=True)
class ControllerTrayActions:
    open_app: Callable[[], None]
    toggle_enabled: Callable[[], None]
    open_settings: Callable[[], None]
    donate: Callable[[], None]
    exit_app: Callable[[], None]


class AppController:
    def __init__(
        self,
        *,
        root,
        settings_store,
        display_provider,
        foreground_provider,
        color_backend,
        tray_backend,
        startup_backend,
        platform_name: str,
        open_url: Callable[[str], object] | None = None,
    ) -> None:
        self.root = root
        self.settings_store = settings_store
        self.display_provider = display_provider
        self.foreground_provider = foreground_provider
        self.color_backend = color_backend
        self.tray_backend = tray_backend
        self.startup_backend = startup_backend
        self.platform_name = platform_name
        self.open_url = open_url or webbrowser.open
        self.version = __version__

        self.displays = self.display_provider.list_displays()
        self.settings = self.settings_store.load(self.displays)
        self.profile_service = ProfileService(self.settings)
        self.activation = ActivationCoordinator(
            self.settings,
            self.profile_service,
            self.color_backend,
            lambda: {display.id: display for display in self.displays},
        )
        self.theme_manager = ThemeManager()
        self.theme_manager.current = self.theme_manager.tokens(self.settings.theme)
        self.update_service = UpdateService()
        self.analytics_service = AnalyticsService()
        self.diagnostics = DiagnosticsCollector(self)
        self.current_foreground = ForegroundProcess(0, "", "")
        self.main_window = None
        self._services_started = False
        self._shutdown = False
        self._ui_queue: queue.SimpleQueue[Callable[[], None]] = queue.SimpleQueue()
        self._ui_pump_scheduled = False
        self._ui_pump_interval_ms = 25

    def _analytics_properties(self) -> dict[str, object]:
        app_dir = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path.cwd()
        edition = detect_edition(app_dir).value
        gpu_vendor = "NVIDIA" if getattr(self.color_backend, "dvc", None) is not None else "Other"
        return {
            "app_version": self.version,
            "edition": edition,
            "windows_version": platform.release() if self.platform_name == "windows" else self.platform_name,
            "gpu_vendor": gpu_vendor,
            "monitor_count": len(self.displays),
        }

    def attach_main_window(self, window) -> None:
        self.main_window = window

    def _ui_call(self, callback: Callable[[], None]) -> None:
        self._ui_queue.put(callback)

    def _schedule_ui_pump(self) -> None:
        if self._shutdown or self._ui_pump_scheduled:
            return
        self._ui_pump_scheduled = True
        self.root.after(self._ui_pump_interval_ms, self._drain_ui_queue)

    def _drain_ui_queue(self) -> None:
        self._ui_pump_scheduled = False
        while True:
            try:
                callback = self._ui_queue.get_nowait()
            except queue.Empty:
                break
            callback()
            if self._shutdown:
                return
        self._schedule_ui_pump()

    def _foreground_callback(self, process: ForegroundProcess) -> None:
        self._ui_call(lambda: self._handle_foreground(process))

    def _handle_foreground(self, process: ForegroundProcess) -> None:
        self.current_foreground = process
        self.activation.on_foreground(process)
        current = self.activation.active_profile_id
        if self.main_window is not None:
            updater = getattr(self.main_window, "update_runtime_status", None)
            if updater:
                updater(process, current)

    def start_services(self) -> None:
        if self._services_started:
            return
        actions = ControllerTrayActions(
            open_app=lambda: self._ui_call(self.open_app),
            toggle_enabled=lambda: self._ui_call(
                lambda: self.set_global_enabled(not self.settings.global_enabled)
            ),
            open_settings=lambda: self._ui_call(self.show_settings),
            donate=lambda: self._ui_call(self.donate),
            exit_app=lambda: self._ui_call(self.shutdown),
        )
        self._schedule_ui_pump()
        self.foreground_provider.start(self._foreground_callback)
        self._handle_foreground(self.foreground_provider.current())
        self.tray_backend.start(actions)
        self.tray_backend.set_enabled(self.settings.global_enabled)
        self._services_started = True
        props = self._analytics_properties()
        self.analytics_service.app_started(self.settings, props)
        if self.analytics_service.daily_active(self.settings, props):
            self.save_settings()

    def set_global_enabled(self, value: bool) -> None:
        self.activation.set_global_enabled(bool(value))
        self.tray_backend.set_enabled(self.settings.global_enabled)
        self.save_settings()

    def set_profile_enabled(self, profile_id: str, value: bool) -> None:
        profile = self.profile_service.get(profile_id)
        profile.enabled = bool(value)
        self.activation.on_foreground(self.current_foreground)
        self.save_settings()
        if self.main_window is not None:
            updater = getattr(self.main_window, "update_profile_status", None)
            if updater:
                updater(profile_id)

    def set_theme(self, mode: ThemeMode) -> None:
        self.settings.theme = ThemeMode(mode)
        self.theme_manager.current = self.theme_manager.tokens(self.settings.theme)

    def save_settings(self) -> None:
        self.settings_store.save(self.settings)

    def refresh_profile(self, profile_id: str) -> None:
        self.activation.refresh_profile(profile_id)
        if self.main_window is not None:
            updater = getattr(self.main_window, "update_profile_status", None)
            if updater:
                updater(profile_id)

    def reload_profile_editor(self, profile_id: str) -> None:
        if self.main_window is not None:
            self.main_window.select_profile(profile_id)

    def on_profile_created(self, profile: GameProfile) -> None:
        if self.main_window is not None:
            self.main_window.select_profile(profile.id)

    def show_add_game(self) -> None:
        from ratvision.ui.add_game_dialog import AddGameDialog

        AddGameDialog(self.root, self)

    def show_copy_settings(self, profile_id: str) -> None:
        from ratvision.ui.profile_tools import CopySettingsDialog

        CopySettingsDialog(self.root, self, profile_id)

    def show_add_process(self, profile_id: str) -> None:
        from tkinter import filedialog

        filename = filedialog.askopenfilename(
            parent=self.root,
            title="Add target process",
            filetypes=[("Windows executable", "*.exe"), ("All files", "*.*")],
        )
        if not filename:
            return
        self.profile_service.add_process(profile_id, Path(filename).name)
        self.save_settings()
        if self.main_window is not None:
            self.main_window.select_profile(profile_id)

    def delete_profile(self, profile_id: str) -> None:
        from tkinter import messagebox

        profile = self.profile_service.get(profile_id)
        if not messagebox.askyesno(
            "Delete profile?",
            f'Remove “{profile.name}” from RAT VISION?\nThe game itself will not be modified.',
            parent=self.root,
        ):
            return
        was_active = self.activation.active_profile_id == profile_id
        if was_active:
            self.color_backend.restore_all()
            self.activation.active_profile_id = None
        self.profile_service.remove_profile(profile_id)
        self.save_settings()
        if self.main_window is not None:
            next_id = self.settings.profiles[0].id if self.settings.profiles else None
            if next_id is None:
                self.main_window.selected_profile_id = None
                self.main_window._build_shell()
            else:
                self.main_window.select_profile(next_id)


    def check_updates_async(self, callback) -> None:
        def worker():
            result = self.update_service.check()
            self._ui_call(lambda: callback(result))
        threading.Thread(target=worker, name="ratvision-update-check", daemon=True).start()

    def apply_update_async(self, result, callback=None) -> None:
        app_dir = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path.cwd()
        def worker():
            outcome = self.update_service.prepare_and_launch(result, app_dir)
            def finish():
                if callback:
                    callback(outcome)
                if getattr(outcome.status, "value", "") == "started":
                    self.shutdown()
            self._ui_call(finish)
        threading.Thread(target=worker, name="ratvision-update-apply", daemon=True).start()

    def show_settings(self) -> None:
        if self.main_window is not None:
            self.main_window.show_settings()

    def open_app(self) -> None:
        for method_name in ("deiconify", "lift"):
            method = getattr(self.root, method_name, None)
            if method:
                method()
        focus = getattr(self.root, "focus_force", None)
        if focus:
            focus()

    def donate(self) -> None:
        self.open_url(DONATION_URL)

    def setting_changed(self, attr: str, value: bool) -> None:
        if attr == "launch_with_windows":
            self.startup_backend.set_enabled(bool(value))
        elif attr == "analytics_enabled":
            self.analytics_service.set_consent(self.settings, bool(value))

    def export_profiles(self) -> None:
        from tkinter import filedialog

        destination = filedialog.asksaveasfilename(
            parent=self.root,
            title="Export RAT VISION profiles",
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
        )
        if destination:
            self.settings_store.export_to(self.settings, Path(destination))

    def import_profiles(self) -> None:
        from tkinter import filedialog, messagebox

        source = filedialog.askopenfilename(
            parent=self.root,
            title="Import RAT VISION profiles",
            filetypes=[("JSON", "*.json"), ("All files", "*.*")],
        )
        if not source:
            return
        try:
            imported = self.settings_store.import_from(Path(source), self.displays)
        except Exception as exc:
            messagebox.showerror("Import failed", str(exc), parent=self.root)
            return
        self.settings.profiles = imported.profiles
        self.save_settings()
        if self.main_window is not None:
            self.main_window.selected_profile_id = self.settings.profiles[0].id if self.settings.profiles else None
            self.main_window._build_shell()

    def restore_default_profiles(self) -> None:
        self.color_backend.restore_all()
        self.activation.active_profile_id = None
        self.settings.profiles = create_default_profiles(self.displays)
        self.save_settings()
        if self.main_window is not None:
            self.main_window.selected_profile_id = self.settings.profiles[0].id if self.settings.profiles else None
            self.main_window._build_shell()

    def copy_diagnostics(self) -> None:
        text = self.diagnostics.format_text()
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        update = getattr(self.root, "update_idletasks", None)
        if update:
            update()

    def open_logs(self) -> None:
        log_dir = self.settings_store.path.parent / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        if sys.platform == "win32" and hasattr(os, "startfile"):
            os.startfile(log_dir)  # type: ignore[attr-defined]

    def shutdown(self) -> None:
        if self._shutdown:
            return
        self._shutdown = True
        try:
            self.foreground_provider.stop()
        finally:
            try:
                self.color_backend.restore_all()
            finally:
                try:
                    self.tray_backend.stop()
                finally:
                    try:
                        self.save_settings()
                    finally:
                        self.root.destroy()
