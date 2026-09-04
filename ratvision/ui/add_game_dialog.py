from __future__ import annotations

from pathlib import Path
import tkinter as tk
from tkinter import filedialog

from ratvision.domain.models import GameProfile, VisualParameters, normalize_executable
from ratvision.platform.processes import ProcessDiscovery, RunningProcess
from ratvision.ui.controls.button import RatButton
from ratvision.ui.controls.checkbox import RatCheckBox
from ratvision.ui.tooltip import attach_tooltip


class AddGameDialog:
    def __init__(self, parent: tk.Misc, controller, *, build_ui: bool = True, discovery: ProcessDiscovery | None = None):
        self.parent = parent
        self.controller = controller
        self.discovery = discovery or ProcessDiscovery()
        self.window: tk.Toplevel | None = None
        self._source_processes: list[str] = []
        self._source_name = ""
        self.display_controls: dict[str, RatCheckBox] = {}
        if build_ui:
            self._build_source_step()

    def _primary_display_ids(self) -> list[str]:
        for display in self.controller.displays:
            if display.primary and display.online:
                return [display.id]
        for display in self.controller.displays:
            if display.online:
                return [display.id]
        return []

    def create_profile(
        self,
        *,
        name: str,
        emoji: str,
        processes: list[str],
        display_ids: list[str] | None = None,
        copy_from_id: str | None = None,
    ) -> GameProfile:
        profile = GameProfile(
            name=name.strip() or "New Game",
            emoji=emoji or "🎮",
            processes=[normalize_executable(value) for value in processes],
            display_ids=list(display_ids if display_ids is not None else self._primary_display_ids()),
            visual=VisualParameters(),
        )
        self.controller.profile_service.add_profile(profile)
        if copy_from_id:
            self.controller.profile_service.copy_visuals(copy_from_id, profile.id)
        self.controller.save_settings()
        callback = getattr(self.controller, "on_profile_created", None)
        if callback:
            callback(profile)
        return profile

    def _new_window(self, title: str) -> tk.Toplevel:
        if self.window is not None and self.window.winfo_exists():
            self.window.destroy()
        self.window = tk.Toplevel(self.parent)
        self.window.title(title)
        self.window.transient(self.parent)
        self.window.grab_set()
        self.window.resizable(False, False)
        theme = self.controller.theme_manager.current
        self.window.configure(background=theme.background)
        return self.window

    def _build_source_step(self) -> None:
        window = self._new_window("Add Game")
        theme = self.controller.theme_manager.current
        tk.Label(window, text="➕  ADD GAME", background=theme.background, foreground=theme.text, font=(theme.font_ui[0], 17, "bold")).pack(anchor="w", padx=24, pady=(22, 0))
        tk.Label(window, text="REGISTER NEW TEST SUBJECT", background=theme.background, foreground=theme.text_muted, font=theme.font_mono).pack(anchor="w", padx=24, pady=(2, 18))
        running_button = RatButton(window, text="🎮  RUNNING APPLICATION", command=self._build_running_list, theme=theme, width=360, height=46)
        running_button.pack(padx=24, pady=5)
        attach_tooltip(running_button, "Choose a process that is currently running and create a profile from it.", theme)
        browse_button = RatButton(window, text="📁  BROWSE FOR .EXE", command=self._browse_exe, theme=theme, width=360, height=46)
        browse_button.pack(padx=24, pady=(5, 24))
        attach_tooltip(browse_button, "Browse directly to a Windows .exe file that should activate the new profile.", theme)

    def _build_running_list(self) -> None:
        window = self._new_window("Choose running application")
        theme = self.controller.theme_manager.current
        tk.Label(window, text="🎮  RUNNING APPLICATIONS", background=theme.background, foreground=theme.text, font=theme.font_display).pack(anchor="w", padx=22, pady=(18, 10))
        search_var = tk.StringVar()
        entry = tk.Entry(window, textvariable=search_var, width=42, background=theme.panel, foreground=theme.text, insertbackground=theme.text, relief="flat")
        entry.pack(fill="x", padx=22, pady=(0, 10))
        attach_tooltip(entry, "Filter the currently running applications by product name or executable.", theme)
        list_frame = tk.Frame(window, background=theme.background)
        list_frame.pack(fill="both", expand=True, padx=22, pady=(0, 20))
        items = self.discovery.list_running()

        def render(*_args):
            for child in list_frame.winfo_children():
                child.destroy()
            needle = search_var.get().lower().strip()
            for item in items:
                if needle and needle not in item.friendly_name.lower() and needle not in item.executable:
                    continue
                RatButton(
                    list_frame,
                    text=f"🎮  {item.friendly_name}   //   {item.executable}",
                    command=lambda p=item: self._select_running(p),
                    theme=theme,
                    width=410,
                ).pack(fill="x", pady=2)
        search_var.trace_add("write", render)
        render()

    def _select_running(self, process: RunningProcess) -> None:
        self._source_processes = [process.executable]
        self._source_name = process.friendly_name
        self._build_profile_step()

    def _browse_exe(self) -> None:
        path = filedialog.askopenfilename(parent=self.window, filetypes=[("Windows executable", "*.exe"), ("All files", "*.*")])
        if not path:
            return
        p = Path(path)
        self._source_processes = [p.name]
        self._source_name = p.stem
        self._build_profile_step()

    def _build_profile_step(self) -> None:
        window = self._new_window("New profile")
        theme = self.controller.theme_manager.current
        tk.Label(window, text="🧬  NEW PROFILE", background=theme.background, foreground=theme.text, font=theme.font_display).pack(anchor="w", padx=24, pady=(20, 14))
        form = tk.Frame(window, background=theme.background)
        form.pack(fill="both", padx=24)
        tk.Label(form, text="🎮 NAME", background=theme.background, foreground=theme.text, font=theme.font_ui).grid(row=0, column=0, sticky="w", pady=6)
        name_var = tk.StringVar(value=self._source_name)
        name_entry = tk.Entry(form, textvariable=name_var, width=34, background=theme.panel, foreground=theme.text, insertbackground=theme.text, relief="flat")
        name_entry.grid(row=0, column=1, pady=6, padx=(12, 0))
        attach_tooltip(name_entry, "Friendly profile name shown in the RAT VISION sidebar.", theme)
        tk.Label(form, text="😀 MARK", background=theme.background, foreground=theme.text, font=theme.font_ui).grid(row=1, column=0, sticky="w", pady=6)
        emoji_var = tk.StringVar(value="🎮")
        emoji_entry = tk.Entry(form, textvariable=emoji_var, width=8, background=theme.panel, foreground=theme.text, insertbackground=theme.text, relief="flat")
        emoji_entry.grid(row=1, column=1, sticky="w", pady=6, padx=(12, 0))
        attach_tooltip(emoji_entry, "Choose a quick visual marker for this profile.", theme)
        tk.Label(form, text="🎯 PROCESS", background=theme.background, foreground=theme.text, font=theme.font_ui).grid(row=2, column=0, sticky="w", pady=6)
        tk.Label(form, text=", ".join(self._source_processes), background=theme.background, foreground=theme.text_muted, font=theme.font_mono).grid(row=2, column=1, sticky="w", pady=6, padx=(12, 0))

        tk.Label(form, text="🖥️ DISPLAYS", background=theme.background, foreground=theme.text, font=theme.font_ui).grid(row=3, column=0, sticky="nw", pady=6)
        display_frame = tk.Frame(form, background=theme.background)
        display_frame.grid(row=3, column=1, sticky="ew", pady=4, padx=(12, 0))
        self.display_controls = {}
        default_ids = set(self._primary_display_ids())
        for display in self.controller.displays:
            label = f"{display.name}   {display.width}×{display.height}" + ("   PRIMARY" if display.primary else "")
            control = RatCheckBox(
                display_frame,
                text=label,
                checked=display.id in default_ids,
                command=None,
                theme=theme,
                width=300,
                height=32,
            )
            control.pack(anchor="w", pady=1)
            self.display_controls[display.id] = control
            attach_tooltip(control, "Include or exclude this monitor from the new profile.", theme)

        options = [("Default", "")] + [(f"{p.emoji} {p.name}", p.id) for p in self.controller.settings.profiles]
        self.starting_profile_by_label = dict(options)
        self.starting_var = tk.StringVar(value="Default")
        tk.Label(form, text="🧪 STARTING", background=theme.background, foreground=theme.text, font=theme.font_ui).grid(row=4, column=0, sticky="w", pady=6)
        self.starting_menu = tk.OptionMenu(form, self.starting_var, *[label for label, _value in options])
        self.starting_menu.configure(background=theme.panel, foreground=theme.text, relief="flat")
        self.starting_menu.grid(row=4, column=1, sticky="ew", pady=6, padx=(12, 0))
        attach_tooltip(self.starting_menu, "Start from defaults or copy visual parameters from an existing profile.", theme)

        def create():
            selected_displays = [display_id for display_id, control in self.display_controls.items() if control.checked]
            copy_from_id = self.starting_profile_by_label.get(self.starting_var.get()) or None
            profile = self.create_profile(
                name=name_var.get(),
                emoji=emoji_var.get(),
                processes=self._source_processes,
                display_ids=selected_displays or self._primary_display_ids(),
                copy_from_id=copy_from_id,
            )
            if self.window:
                self.window.destroy()
            return profile

        create_button = RatButton(window, text="CREATE PROFILE", command=create, theme=theme, width=190, height=40)
        create_button.pack(anchor="e", padx=24, pady=(18, 24))
        attach_tooltip(create_button, "Create the profile and save it immediately.", theme)
