from __future__ import annotations

import tkinter as tk

from ratvision import __version__
from ratvision.domain.models import ThemeMode
from ratvision.ui.controls.led import RatLed
from ratvision.ui.assets import AssetManager
from ratvision.ui.controls.toggle import RatToggle
from ratvision.ui.profile_workspace import ProfileWorkspace
from ratvision.ui.sidebar import Sidebar
from ratvision.ui.settings_view import SettingsView
from ratvision.ui.tooltip import attach_tooltip
from ratvision.ui.tour import TourStep, TutorialTour


class MainWindow:
    def __init__(self, root: tk.Tk, controller):
        self.root = root
        self.controller = controller
        self.selected_profile_id = controller.settings.profiles[0].id if controller.settings.profiles else None
        self.sidebar = None
        self.workspace = None
        self.global_toggle = None
        self.settings_view = None
        self.asset_manager = AssetManager(root)
        self.brand_image = None
        self.app_icon_image = None
        self.brand_label = None
        self.tour = None
        self._build_shell()
        self.root.bind_all("<MouseWheel>", self._on_mousewheel, add="+")
        self.root.bind_all("<Button-4>", self._on_mousewheel, add="+")
        self.root.bind_all("<Button-5>", self._on_mousewheel, add="+")

    def _build_shell(self):
        if self.tour is not None and self.tour.active:
            self.tour.finish()
        for child in self.root.winfo_children():
            child.destroy()
        self.root.title(f"RAT VISION v{__version__}")
        self.root.geometry("1180x760")
        self.root.minsize(980, 640)
        theme = self.controller.theme_manager.apply(self.root, self.controller.settings.theme)
        try:
            self.root.attributes("-topmost", bool(self.controller.settings.always_on_top))
        except tk.TclError:
            pass

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(1, weight=1)

        top = tk.Frame(self.root, background=theme.panel, height=74, highlightthickness=1, highlightbackground=theme.border)
        top.grid(row=0, column=0, sticky="ew")
        top.grid_propagate(False)
        left = tk.Frame(top, background=theme.panel)
        left.pack(side="left", padx=16, pady=8)
        brand = self.asset_manager.semantic("brand", 48)
        self.brand_image = brand.image
        self.brand_label = tk.Label(
            left,
            image=self.brand_image or "",
            text="" if self.brand_image else brand.glyph,
            background=theme.panel,
            foreground=theme.text,
            bd=0,
        )
        self.brand_label.pack(side="left", padx=(0, 10))
        text_block = tk.Frame(left, background=theme.panel)
        text_block.pack(side="left")
        tk.Label(text_block, text=f"RAT VISION v{__version__}", background=theme.panel, foreground=theme.text, font=(theme.font_ui[0], 16, "bold")).pack(anchor="w")
        tk.Label(text_block, text="VISUAL SYSTEMS // INTERNAL PROTOCOL", background=theme.panel, foreground=theme.text_muted, font=theme.font_mono).pack(anchor="w")
        self.app_icon_image = self.asset_manager.get("brand/ratvision_icon.png", 64)
        icon_image = self.app_icon_image or self.brand_image
        if icon_image:
            try:
                self.root.iconphoto(True, icon_image)
            except tk.TclError:
                pass

        right = tk.Frame(top, background=theme.panel)
        right.pack(side="right", padx=18, pady=12)
        self.tour_button = tk.Label(
            right,
            text="❔ TOUR",
            background=theme.panel,
            foreground=theme.text_muted,
            font=theme.font_mono,
            cursor="hand2",
            padx=6,
            pady=4,
        )
        self.tour_button.pack(side="left", padx=(0, 12))
        self.tour_button.bind("<Button-1>", lambda _e: self.start_tour())
        attach_tooltip(self.tour_button, "Start a guided 60-second tour of RAT VISION.", theme)
        self.pin_button = tk.Label(
            right,
            text="📌",
            background=theme.panel,
            foreground=theme.text if self.controller.settings.always_on_top else theme.text_muted,
            font=(theme.font_ui[0], 15),
            cursor="hand2",
            padx=4,
        )
        self.pin_button.pack(side="left", padx=(0, 10))
        self.pin_button.bind("<Button-1>", lambda _e: self.toggle_always_on_top())
        attach_tooltip(
            self.pin_button,
            "Keep RAT VISION above other windows. This affects only the window position and does not change profile activation or full-screen games.",
            theme,
        )
        self.theme_button = tk.Label(
            right,
            text="☀️" if self.controller.settings.theme != ThemeMode.DAY else "🌙",
            background=theme.panel,
            foreground=theme.text,
            font=(theme.font_ui[0], 16),
            cursor="hand2",
        )
        self.theme_button.pack(side="left", padx=(0, 16))
        self.theme_button.bind("<Button-1>", lambda _e: self.toggle_theme())
        attach_tooltip(self.theme_button, "Switch between Clean Lab day mode and Level Black night mode.", theme)
        tk.Label(right, text="XRAT TRACING", background=theme.panel, foreground=theme.text, font=theme.font_display).pack(side="left", padx=(0, 8))
        self.global_led = RatLed(right, on=self.controller.settings.global_enabled, theme=theme)
        self.global_led.pack(side="left", padx=(0, 6))
        self.global_toggle = RatToggle(
            right,
            value=self.controller.settings.global_enabled,
            command=self._set_global_enabled,
            theme=theme,
        )
        self.global_toggle.pack(side="left")
        attach_tooltip(self.global_toggle, "Master switch for automatic RAT VISION profile application.", theme)

        body = tk.Frame(self.root, background=theme.background)
        body.grid(row=1, column=0, sticky="nsew")
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        self.sidebar = Sidebar(
            body,
            profiles=self.controller.settings.profiles,
            selected_profile_id=self.selected_profile_id,
            theme=theme,
            on_select=self.select_profile,
            on_toggle=self.controller.set_profile_enabled,
            on_add_game=self.controller.show_add_game,
            on_donate=self.controller.donate,
            on_settings=self.controller.show_settings,
            on_tour=self.start_tour,
            show_tour_hint=not self.controller.settings.tour_prompt_seen,
            on_dismiss_tour_hint=self.dismiss_tour_hint,
        )
        self.sidebar.grid(row=0, column=0, sticky="ns")

        workspace_outer = tk.Frame(body, background=theme.background)
        workspace_outer.grid(row=0, column=1, sticky="nsew")
        workspace_outer.rowconfigure(0, weight=1)
        workspace_outer.columnconfigure(0, weight=1)
        self.workspace_canvas = tk.Canvas(workspace_outer, background=theme.background, highlightthickness=0, bd=0)
        scrollbar = tk.Scrollbar(workspace_outer, orient="vertical", command=self.workspace_canvas.yview)
        self.workspace_canvas.configure(yscrollcommand=scrollbar.set)
        self.workspace_canvas.grid(row=0, column=0, sticky="nsew")
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.workspace_host = tk.Frame(self.workspace_canvas, background=theme.background)
        self.workspace_window = self.workspace_canvas.create_window((0, 0), window=self.workspace_host, anchor="nw")
        self.workspace_host.bind("<Configure>", self._sync_scrollregion)
        self.workspace_canvas.bind("<Configure>", self._sync_workspace_width)
        self._build_workspace(theme)


    def show_settings(self):
        theme = self.controller.theme_manager.current
        for child in self.workspace_host.winfo_children():
            child.destroy()
        self.workspace = None
        self.settings_view = SettingsView(self.workspace_host, self.controller)
        self.settings_view.pack(fill="both", expand=True, padx=34, pady=(26, 34))
        self._sync_scrollregion()

    def update_runtime_status(self, process, active_profile_id: str | None):
        if self.workspace is None:
            return
        if active_profile_id == self.workspace.profile.id:
            text = "● LIVE // PROFILE CURRENTLY APPLIED"
            color = self.controller.theme_manager.current.status_on
        elif process.executable and process.executable in self.workspace.profile.processes:
            text = "○ PROCESS DETECTED // WAITING FOR FOCUS"
            color = self.controller.theme_manager.current.text_muted
        else:
            text = "○ READY"
            color = self.controller.theme_manager.current.text_muted
        self.workspace.runtime_status.configure(text=text, foreground=color)

    def update_profile_status(self, profile_id: str):
        if self.workspace is not None and self.workspace.profile.id == profile_id:
            active = self.controller.activation.active_profile_id
            self.update_runtime_status(self.controller.current_foreground, active)


    def _is_workspace_widget(self, widget) -> bool:
        current = widget
        while current is not None:
            if current is self.workspace_canvas or current is self.workspace_host:
                return True
            current = getattr(current, "master", None)
        return False

    def _on_mousewheel(self, event):
        if not hasattr(self, "workspace_canvas") or not self._is_workspace_widget(getattr(event, "widget", None)):
            return None
        number = getattr(event, "num", None)
        if number == 4:
            steps = -1
        elif number == 5:
            steps = 1
        else:
            delta = int(getattr(event, "delta", 0) or 0)
            if delta == 0:
                return None
            if abs(delta) >= 120:
                steps = -int(delta / 120)
            else:
                steps = -1 if delta > 0 else 1
        self.workspace_canvas.yview_scroll(steps, "units")
        return "break"

    def _sync_scrollregion(self, _event=None):
        self.workspace_canvas.configure(scrollregion=self.workspace_canvas.bbox("all"))

    def _sync_workspace_width(self, event):
        self.workspace_canvas.itemconfigure(self.workspace_window, width=max(600, event.width))

    def _build_workspace(self, theme):
        for child in self.workspace_host.winfo_children():
            child.destroy()
        if not self.controller.settings.profiles:
            tk.Label(
                self.workspace_host,
                text="🐀  NO TEST SUBJECTS REGISTERED\nAdd a game to begin XRAT testing.",
                background=theme.background,
                foreground=theme.text,
                font=(theme.font_ui[0], 14),
                justify="left",
            ).pack(anchor="nw", padx=34, pady=34)
            self.workspace = None
            return
        try:
            profile = self.controller.profile_service.get(self.selected_profile_id)
        except (KeyError, TypeError):
            profile = self.controller.settings.profiles[0]
            self.selected_profile_id = profile.id
        self.workspace = ProfileWorkspace(
            self.workspace_host,
            self.controller,
            profile,
            self.controller.displays,
            theme,
        )
        self.workspace.pack(fill="both", expand=True, padx=34, pady=(26, 34))

    def select_profile(self, profile_id: str):
        self.selected_profile_id = profile_id
        self.settings_view = None
        self._build_shell()

    def dismiss_tour_hint(self):
        self.controller.settings.tour_prompt_seen = True
        self.controller.save_settings()
        if self.sidebar is not None and self.sidebar.tour_hint is not None:
            self.sidebar.tour_hint.destroy()
            self.sidebar.tour_hint = None

    def start_tour(self):
        self.controller.settings.tour_prompt_seen = True
        self.controller.save_settings()
        specific = next((profile for profile in self.controller.settings.profiles if profile.builtin_id != "global"), None)
        if specific is not None and self.selected_profile_id != specific.id:
            self.selected_profile_id = specific.id
            self.settings_view = None
            self._build_shell()
        elif self.sidebar is not None and self.sidebar.tour_hint is not None:
            self.sidebar.tour_hint.destroy()
            self.sidebar.tour_hint = None

        global_row = next((row for row in self.sidebar.profile_rows if row.profile.builtin_id == "global"), None) if self.sidebar else None
        game_row = next((row for row in self.sidebar.profile_rows if row.profile.builtin_id != "global"), None) if self.sidebar else None
        workspace = self.workspace
        first_display = next(iter(workspace.display_checks.values()), None) if workspace is not None else None
        process_target = None
        if workspace is not None:
            process_target = workspace.process_rows[0].frame if workspace.process_rows else getattr(workspace, "add_process_button", None)
        steps = [
            TourStep(lambda: self.global_toggle, "XRAT TRACING", "Master automation switch. Turn it off to restore normal monitor colors and pause all profile application."),
            TourStep(lambda: global_row, "GLOBAL PROFILE", "Process-independent fallback. It is applied whenever no enabled game profile matches the foreground application."),
            TourStep(lambda: game_row, "GAME PROFILES", "Each game can have its own visual parameters, target processes and selected monitors."),
            TourStep(lambda: game_row.toggle if game_row else None, "QUICK PROFILE SWITCH", "Enable or disable a profile directly from the sidebar without opening it."),
            TourStep(lambda: workspace.parameter_sliders.get("brightness") if workspace else None, "VISUAL PARAMETERS", "Brightness, contrast, gamma and NVIDIA Digital Vibrance are saved independently per profile."),
            TourStep(lambda: first_display, "DISPLAYS", "Choose exactly which monitor or monitors this profile can modify."),
            TourStep(lambda: process_target, "TARGET PROCESSES", "A game profile activates when one of these .exe processes owns the foreground window."),
            TourStep(lambda: workspace.copy_button if workspace else None, "COPY SETTINGS", "Copy only visual parameters from another profile while keeping this profile's processes and displays."),
            TourStep(lambda: self.sidebar.add_game_button if self.sidebar else None, "ADD GAME", "Create a new profile from a running application or browse directly to an .exe file."),
            TourStep(lambda: self.brand_label, "TRAY MODE", "Closing the window can leave RAT VISION running in the system tray. Click the tray icon to bring it back."),
        ]
        self.tour = TutorialTour(self.root, self.controller.theme_manager.current, steps)
        self.tour.start()

    def _set_global_enabled(self, value: bool):
        self.controller.set_global_enabled(value)
        if self.global_led:
            self.global_led.set(value)

    def toggle_always_on_top(self):
        enabled = not bool(self.controller.settings.always_on_top)
        self.controller.settings.always_on_top = enabled
        try:
            self.root.attributes("-topmost", enabled)
        except tk.TclError:
            pass
        theme = self.controller.theme_manager.current
        if hasattr(self, "pin_button"):
            self.pin_button.configure(foreground=theme.text if enabled else theme.text_muted)
        self.controller.save_settings()

    def toggle_theme(self):
        current = self.controller.settings.theme
        next_mode = ThemeMode.NIGHT if current == ThemeMode.DAY else ThemeMode.DAY
        self.controller.set_theme(next_mode)
        self.controller.save_settings()
        self._build_shell()
