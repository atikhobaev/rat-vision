from __future__ import annotations

import tkinter as tk
from tkinter import messagebox

from ratvision import __version__
from ratvision.domain.models import ThemeMode
from ratvision.updates.service import UpdateStatus
from ratvision.ui.controls.button import RatButton
from ratvision.ui.controls.checkbox import RatCheckBox
from ratvision.ui.tooltip import attach_tooltip


class SettingsView(tk.Frame):
    def __init__(self, master, controller, *, info_sink=None):
        self.controller = controller
        self.theme = controller.theme_manager.current
        self.info_sink = info_sink or (lambda title, msg: messagebox.showinfo(title, msg, parent=self.winfo_toplevel()))
        self.controls = {}
        super().__init__(master, background=self.theme.background)
        self._build()

    def _section(self, title: str):
        frame = tk.Frame(self, background=self.theme.background)
        frame.pack(fill="x", pady=(18, 4))
        tk.Label(
            frame,
            text=title,
            background=self.theme.background,
            foreground=self.theme.text,
            font=self.theme.font_display,
            anchor="w",
        ).pack(fill="x")
        return frame

    def _checkbox(self, master, text: str, attr: str):
        control = RatCheckBox(
            master,
            text=text,
            checked=bool(getattr(self.controller.settings, attr)),
            command=lambda value: self._set_bool(attr, value),
            theme=self.theme,
            width=620,
        )
        control.pack(anchor="w", pady=2)
        help_text = {
            "launch_with_windows": "Start RAT VISION automatically when you sign in to Windows.",
            "start_minimized": "Launch directly into tray mode instead of opening the main window.",
            "close_to_tray": "Closing the window hides it to the tray instead of exiting RAT VISION.",
        }.get(attr, text)
        attach_tooltip(control, help_text, self.theme)
        self.controls[attr] = control
        return control

    def _build(self):
        tk.Label(self, text="⚙️  SETTINGS", background=self.theme.background, foreground=self.theme.text, font=(self.theme.font_ui[0], 20, "bold")).pack(anchor="w")
        tk.Label(self, text="SYSTEM CONFIGURATION", background=self.theme.background, foreground=self.theme.text_muted, font=self.theme.font_mono).pack(anchor="w", pady=(2, 4))

        startup = self._section("🚀  STARTUP")
        self._checkbox(startup, "Launch RAT VISION with Windows", "launch_with_windows")
        self._checkbox(startup, "Start minimized to tray", "start_minimized")

        window_behavior = self._section("🪟  WINDOW BEHAVIOR")
        self._checkbox(window_behavior, "Closing the window minimizes to tray", "close_to_tray")

        profile_data = self._section("🧪  PROFILE DATA")
        button_row = tk.Frame(profile_data, background=self.theme.background)
        button_row.pack(anchor="w", pady=4)
        for text, callback, width in (
            ("📤 Export profiles", self.controller.export_profiles, 170),
            ("📥 Import profiles", self.controller.import_profiles, 170),
            ("🔄 Restore defaults", self.controller.restore_default_profiles, 180),
        ):
            RatButton(button_row, text=text, command=callback, theme=self.theme, width=width).pack(side="left", padx=(0, 8))

        appearance = self._section("🎨  APPEARANCE")
        self.theme_var = tk.StringVar(value=self.controller.settings.theme.value)
        for label, value in (
            ("🖥️ Follow Windows", ThemeMode.SYSTEM.value),
            ("☀️ Day // Clean Lab", ThemeMode.DAY.value),
            ("🌙 Night // Level Black", ThemeMode.NIGHT.value),
        ):
            radio = tk.Radiobutton(
                appearance,
                text=label,
                value=value,
                variable=self.theme_var,
                command=lambda v=value: self._set_theme(v),
                background=self.theme.background,
                foreground=self.theme.text,
                activebackground=self.theme.background,
                activeforeground=self.theme.text,
                selectcolor=self.theme.panel,
                font=self.theme.font_ui,
                anchor="w",
            )
            radio.pack(anchor="w")
            attach_tooltip(radio, "Choose how RAT VISION selects its interface theme.", self.theme)

        diagnostics = self._section("📋  SYSTEM STATUS")
        info = tk.Label(
            diagnostics,
            text=f"Displays detected: {len(self.controller.displays)}",
            background=self.theme.background,
            foreground=self.theme.text_muted,
            font=self.theme.font_mono,
            anchor="w",
        )
        info.pack(anchor="w", pady=(2, 6))
        diag_actions = tk.Frame(diagnostics, background=self.theme.background)
        diag_actions.pack(anchor="w")
        RatButton(diag_actions, text="📋 Copy diagnostics", command=self.controller.copy_diagnostics, theme=self.theme, width=170).pack(side="left", padx=(0, 8))
        RatButton(diag_actions, text="📁 Open logs", command=self.controller.open_logs, theme=self.theme, width=140).pack(side="left")

        updates = self._section("🔄  UPDATES")
        channel = "Public beta" if "-" in __version__ else "Stable"
        tk.Label(updates, text=f"Current version   RAT VISION v{__version__}", background=self.theme.background, foreground=self.theme.text, font=self.theme.font_mono).pack(anchor="w")
        tk.Label(updates, text=f"Update channel    {channel}", background=self.theme.background, foreground=self.theme.text_muted, font=self.theme.font_mono).pack(anchor="w", pady=(0, 4))
        self.update_status_label = tk.Label(updates, text="Ready to check GitHub Releases", background=self.theme.background, foreground=self.theme.text_muted, font=self.theme.font_mono, anchor="w")
        self.update_status_label.pack(anchor="w", pady=(0, 7))
        row = tk.Frame(updates, background=self.theme.background); row.pack(anchor="w")
        self.update_button = RatButton(row, text="🔄 Check for updates", command=self._check_updates, theme=self.theme, width=190)
        self.update_button.pack(side="left", padx=(0,8))
        self.update_apply_button = RatButton(row, text="⬇ Download & Update", command=self._apply_update, theme=self.theme, width=190)
        self._last_update_result = None
        attach_tooltip(self.update_button, "Check the configured public GitHub Releases stream for a newer eligible build.", self.theme)
        attach_tooltip(self.update_apply_button, "Download the matching Installer/Portable asset, verify SHA-256, then apply it.", self.theme)

        analytics_service = getattr(self.controller, "analytics_service", None)
        if analytics_service is not None and analytics_service.configured:
            analytics = self._section("📊  ANONYMOUS ANALYTICS")
            control = self._checkbox(analytics, "Share anonymous usage statistics", "analytics_enabled")
            attach_tooltip(control, "Enabled by default and can be turned off at any time. Sends only coarse app/version/edition activity data; never game names, process names, paths or personal identifiers.", self.theme)
            tk.Label(analytics, text="Enabled by default • turn off any time\nWhat is collected?  app version • edition • Windows bucket • GPU vendor • monitor count • daily activity", background=self.theme.background, foreground=self.theme.text_muted, font=self.theme.font_mono, anchor="w", justify="left").pack(anchor="w", pady=(2,0))

        about = self._section("ℹ️  ABOUT")
        self.about_version_label = tk.Label(about, text=f"🐀  RAT VISION  v{__version__}", background=self.theme.background, foreground=self.theme.text, font=(self.theme.font_ui[0], 13, "bold"), anchor="w")
        self.about_version_label.pack(anchor="w")
        tk.Label(about, text="See what the rat sees.", background=self.theme.background, foreground=self.theme.text_muted, font=self.theme.font_ui).pack(anchor="w")
        tk.Label(about, text="🧪 XRAT TRACING  //  Experimental Rodent Visual Enhancement Technology", background=self.theme.background, foreground=self.theme.text_muted, font=self.theme.font_mono).pack(anchor="w", pady=(6, 0))
        tk.Label(about, text="Powered by questionable research.", background=self.theme.background, foreground=self.theme.text_muted, font=self.theme.font_ui).pack(anchor="w", pady=(2, 8))

    def _set_bool(self, attr: str, value: bool):
        callback = getattr(self.controller, "setting_changed", None)
        if callback:
            callback(attr, bool(value))
        setattr(self.controller.settings, attr, bool(value))
        self.controller.save_settings()

    def _set_theme(self, raw: str):
        mode = ThemeMode(raw)
        self.controller.set_theme(mode)
        self.controller.save_settings()

    def _check_updates(self):
        self.update_status_label.configure(text="Checking GitHub Releases…")
        checker = getattr(self.controller, "check_updates_async", None)
        if checker:
            checker(self._handle_update_result)
        else:
            self._handle_update_result(self.controller.update_service.check())

    def _handle_update_result(self, result):
        self._last_update_result = result
        self.update_status_label.configure(text=result.message)
        if result.status is UpdateStatus.AVAILABLE:
            self.update_apply_button.pack(side="left")
        else:
            self.update_apply_button.pack_forget()
        self.info_sink(result.title, result.message)

    def _apply_update(self):
        result = self._last_update_result
        if result is None or result.status is not UpdateStatus.AVAILABLE:
            return
        if not messagebox.askyesno("Install update?", f"Download and install RAT VISION v{result.release.version}?", parent=self.winfo_toplevel()):
            return
        self.update_status_label.configure(text="Downloading and verifying update…")
        applier = getattr(self.controller, "apply_update_async", None)
        if applier:
            applier(result, self._handle_update_result)
