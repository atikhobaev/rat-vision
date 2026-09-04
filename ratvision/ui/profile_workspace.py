from __future__ import annotations

from dataclasses import dataclass, replace
import tkinter as tk

from ratvision.domain.models import DisplayInfo, GameProfile, VisualParameters
from ratvision.ui.controls.button import RatButton
from ratvision.ui.controls.checkbox import RatCheckBox
from ratvision.ui.controls.slider import RatSlider
from ratvision.ui.theme import ThemeTokens
from ratvision.ui.tooltip import attach_tooltip


@dataclass(slots=True)
class ProcessRow:
    frame: tk.Frame
    executable: str


class ProfileWorkspace(tk.Frame):
    PARAMS = (
        ("brightness", "☀️  BRIGHTNESS", 0.0, 1.0, 0.5, ".2f"),
        ("contrast", "◐  CONTRAST", 0.0, 1.0, 0.5, ".2f"),
        ("gamma", "🌗  GAMMA", 0.4, 2.8, 1.0, ".2f"),
        ("saturation", "🎨  SATURATION", 0.0, 100.0, 0.0, ".0f"),
    )

    def __init__(self, master, controller, profile: GameProfile, displays: list[DisplayInfo], theme: ThemeTokens):
        super().__init__(master, background=theme.background)
        self.controller = controller
        self.profile = profile
        self.displays = displays
        self.theme = theme
        self.parameter_sliders: dict[str, RatSlider] = {}
        self.parameter_value_labels: dict[str, tk.Label] = {}
        self.display_checks: dict[str, RatCheckBox] = {}
        self.process_rows: list[ProcessRow] = []
        self._build()

    def _label(self, master, text, *, size=10, bold=False, muted=False, mono=False, **grid):
        if mono:
            font = self.theme.font_mono
        else:
            font = (self.theme.font_ui[0], size, "bold" if bold else "normal")
        label = tk.Label(
            master,
            text=text,
            background=master.cget("background"),
            foreground=self.theme.text_muted if muted else self.theme.text,
            font=font,
            anchor="w",
        )
        if grid:
            label.grid(**grid)
        return label

    def _section_title(self, text, row):
        label = tk.Label(
            self,
            text=text,
            background=self.theme.background,
            foreground=self.theme.text,
            font=self.theme.font_display,
            anchor="w",
        )
        label.grid(row=row, column=0, columnspan=4, sticky="ew", pady=(12, 6))
        return label

    def _build(self):
        self.columnconfigure(1, weight=1)
        is_global = self.profile.builtin_id == "global"
        profile_code = "GLOBAL" if is_global else "PROFILE // 01"
        self._label(self, profile_code, muted=True, mono=True, row=0, column=0, columnspan=4, sticky="w")
        self._label(self, f"{self.profile.emoji}  {self.profile.name.upper()}", size=18, bold=True, row=1, column=0, columnspan=4, sticky="w", pady=(5, 2))
        target_summary = "🌐  PROCESS INDEPENDENT // DESKTOP FALLBACK" if is_global else f"🎯  {self.profile.processes[0] if self.profile.processes else 'NO TARGET PROCESS'}"
        self.target_summary_label = self._label(self, target_summary, muted=True, mono=True, row=2, column=0, columnspan=4, sticky="w")
        if is_global:
            attach_tooltip(
                self.target_summary_label,
                "Global is process-independent: it acts as the fallback when no enabled game profile matches. Its own switch controls only Global; XRAT TRACING disables or enables the whole profile engine.",
                self.theme,
            )
        self.runtime_status = self._label(self, "○ READY", muted=True, mono=True, row=3, column=0, columnspan=4, sticky="w", pady=(4, 2))

        row = 4
        self._section_title("👁️  VISUAL PARAMETERS", row)
        row += 1
        for key, title, minimum, maximum, default, fmt in self.PARAMS:
            self._label(self, title, bold=True, row=row, column=0, sticky="w", padx=(0, 14), pady=2)
            current = float(getattr(self.profile.visual, key))
            slider = RatSlider(
                self,
                value=current,
                minimum=minimum,
                maximum=maximum,
                command=lambda value, k=key: self._set_parameter(k, value),
                theme=self.theme,
                width=390,
                height=28,
            )
            slider.grid(row=row, column=1, sticky="ew", pady=2)
            self.parameter_sliders[key] = slider
            parameter_help = {
                "brightness": "Changes overall brightness for the selected monitors in this profile.",
                "contrast": "Changes the separation between darker and brighter tones.",
                "gamma": "Adjusts mid-tones without changing every level uniformly.",
                "saturation": "NVIDIA Digital Vibrance. Changes color saturation through the NVIDIA driver when supported.",
            }[key]
            attach_tooltip(slider, parameter_help, self.theme)
            value_label = self._label(self, format(current, fmt), mono=True, row=row, column=2, padx=(14, 10), sticky="e")
            self.parameter_value_labels[key] = value_label
            reset = RatButton(
                self,
                text="↺",
                command=lambda k=key, d=default: self._reset_parameter(k, d),
                theme=self.theme,
                width=36,
                height=26,
            )
            reset.grid(row=row, column=3, sticky="e")
            attach_tooltip(reset, f"Reset {title.replace('☀️  ', '').replace('◐  ', '').replace('🌗  ', '').replace('🎨  ', '').lower()} to its default value.", self.theme)
            row += 1

        self._section_title("🧪  PROFILE TOOLS", row)
        row += 1
        tools = tk.Frame(self, background=self.theme.background)
        tools.grid(row=row, column=0, columnspan=4, sticky="w")
        self.copy_button = RatButton(tools, text="🧬 Copy settings from...", command=self._copy_stub, theme=self.theme, width=220, height=32)
        self.copy_button.pack(side="left", padx=(0, 8))
        attach_tooltip(self.copy_button, "Copy only visual parameters from another profile.", self.theme)
        self.reset_button = RatButton(tools, text="🔄 Reset all", command=self._reset_all, theme=self.theme, width=140, height=32)
        self.reset_button.pack(side="left")
        attach_tooltip(self.reset_button, "Reset all visual parameters in this profile to defaults.", self.theme)
        row += 1

        self._section_title("🖥️  DISPLAYS", row)
        row += 1
        for display in self.displays:
            suffix = "   PRIMARY" if display.primary else ""
            offline = "   OFFLINE" if not display.online else ""
            refresh = f" · {display.refresh_hz:g} Hz" if display.refresh_hz else ""
            text = f"{display.name}{suffix}{offline}   {display.width}×{display.height}{refresh}   // {display.id}"
            check = RatCheckBox(
                self,
                text=text,
                checked=display.id in self.profile.display_ids,
                command=lambda checked, d=display.id: self._set_display(d, checked),
                theme=self.theme,
                width=650,
                height=34,
            )
            check.grid(row=row, column=0, columnspan=4, sticky="ew", pady=1)
            self.display_checks[display.id] = check
            attach_tooltip(check, "Toggle whether this profile is allowed to change this monitor.", self.theme)
            row += 1

        if not is_global:
            self._section_title("🎯  TARGET PROCESSES", row)
            row += 1
            for executable in self.profile.processes:
                frame = tk.Frame(self, background=self.theme.panel, highlightthickness=1, highlightbackground=self.theme.border)
                frame.grid(row=row, column=0, columnspan=4, sticky="ew", pady=2)
                label = tk.Label(frame, text=executable, font=self.theme.font_mono, background=self.theme.panel, foreground=self.theme.text)
                label.pack(side="left", padx=12, pady=5)
                remove = tk.Label(frame, text="✕", font=self.theme.font_ui, background=self.theme.panel, foreground=self.theme.text_muted, cursor="hand2")
                remove.pack(side="right", padx=12)
                remove.bind("<Button-1>", lambda _e, exe=executable: self._remove_process(exe))
                attach_tooltip(remove, "Remove this .exe from the profile. The profile may have zero target processes.", self.theme)
                self.process_rows.append(ProcessRow(frame, executable))
                row += 1
            self.add_process_button = RatButton(self, text="➕ Add process", command=self._add_process_stub, theme=self.theme, width=160, height=32)
            self.add_process_button.grid(row=row, column=0, sticky="w", pady=(5, 2))
            attach_tooltip(self.add_process_button, "Add another .exe that can activate this profile.", self.theme)
            row += 1

        footer = tk.Frame(self, background=self.theme.background)
        footer.grid(row=row, column=0, columnspan=4, sticky="ew", pady=(12, 4))
        footer_text = "🌐 XRAT-GLOBAL // FALLBACK READY" if is_global else f"🧬 XRAT-VS/{self.profile.id[:4].upper()} // PROFILE READY"
        self._label(footer, footer_text, muted=True, mono=True).pack(side="left")
        if not is_global:
            self.delete_button = RatButton(footer, text="🗑 Delete profile", command=self._delete_stub, theme=self.theme, width=150, height=32, danger=True)
            self.delete_button.pack(side="right")
            attach_tooltip(self.delete_button, "Delete this profile after confirmation. The game itself is not modified.", self.theme)

    def _set_parameter(self, key: str, value: float):
        if key == "saturation":
            value = int(round(value))
        self.profile.visual = replace(self.profile.visual, **{key: value}).normalized()
        actual = getattr(self.profile.visual, key)
        fmt = next(item[5] for item in self.PARAMS if item[0] == key)
        if key in self.parameter_value_labels:
            self.parameter_value_labels[key].configure(text=format(float(actual), fmt))
        self.controller.save_settings()
        self.controller.refresh_profile(self.profile.id)

    def _reset_parameter(self, key: str, default: float):
        self.parameter_sliders[key].set(default)
        self._set_parameter(key, default)

    def _reset_all(self):
        defaults = VisualParameters()
        for key, _title, _minimum, _maximum, _default, _fmt in self.PARAMS:
            value = getattr(defaults, key)
            self.parameter_sliders[key].set(value)
        self.profile.visual = defaults
        for key, label in self.parameter_value_labels.items():
            fmt = next(item[5] for item in self.PARAMS if item[0] == key)
            label.configure(text=format(float(getattr(defaults, key)), fmt))
        self.controller.save_settings()
        self.controller.refresh_profile(self.profile.id)

    def _set_display(self, display_id: str, checked: bool):
        current = list(self.profile.display_ids)
        if checked and display_id not in current:
            current.append(display_id)
        elif not checked and display_id in current:
            if self.profile.enabled and len(current) <= 1:
                self.display_checks[display_id].set(True)
                return
            current.remove(display_id)
        self.controller.profile_service.set_displays(self.profile.id, current)
        self.controller.save_settings()
        self.controller.refresh_profile(self.profile.id)

    def _remove_process(self, executable: str):
        self.controller.profile_service.remove_process(self.profile.id, executable)
        self.controller.save_settings()
        self.controller.refresh_profile(self.profile.id)
        reload_editor = getattr(self.controller, "reload_profile_editor", None)
        if reload_editor:
            reload_editor(self.profile.id)

    def _copy_stub(self):
        callback = getattr(self.controller, "show_copy_settings", None)
        if callback:
            callback(self.profile.id)

    def _add_process_stub(self):
        callback = getattr(self.controller, "show_add_process", None)
        if callback:
            callback(self.profile.id)

    def _delete_stub(self):
        callback = getattr(self.controller, "delete_profile", None)
        if callback:
            callback(self.profile.id)
