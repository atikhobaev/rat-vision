from __future__ import annotations

import tkinter as tk

from ratvision.ui.controls.button import RatButton
from ratvision.ui.tooltip import attach_tooltip


class CopySettingsDialog:
    def __init__(self, parent: tk.Misc, controller, target_profile_id: str):
        self.controller = controller
        self.target_profile_id = target_profile_id
        self.window = tk.Toplevel(parent)
        self.window.title("Copy visual parameters")
        self.window.transient(parent)
        self.window.grab_set()
        theme = controller.theme_manager.current
        self.window.configure(background=theme.background)
        tk.Label(
            self.window,
            text="🧪  COPY VISUAL PARAMETERS FROM",
            background=theme.background,
            foreground=theme.text,
            font=theme.font_display,
        ).pack(anchor="w", padx=20, pady=(18, 12))
        for profile in controller.settings.profiles:
            if profile.id == target_profile_id:
                continue
            button = RatButton(
                self.window,
                text=f"{profile.emoji}  {profile.name}",
                command=lambda source_id=profile.id: self._copy(source_id),
                theme=theme,
                width=300,
            )
            button.pack(fill="x", padx=20, pady=3)
            attach_tooltip(button, f"Copy visual parameters from {profile.name}. Processes and displays stay unchanged.", theme)

    def _copy(self, source_id: str) -> None:
        self.controller.profile_service.copy_visuals(source_id, self.target_profile_id)
        self.controller.save_settings()
        self.controller.refresh_profile(self.target_profile_id)
        reload_editor = getattr(self.controller, "reload_profile_editor", None)
        if reload_editor:
            reload_editor(self.target_profile_id)
        self.window.destroy()
