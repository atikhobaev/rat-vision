from __future__ import annotations

import tkinter as tk

from ratvision.domain.models import GameProfile
from ratvision.ui.controls.button import RatButton
from ratvision.ui.controls.toggle import RatToggle
from ratvision.ui.assets import AssetManager
from ratvision.ui.theme import ThemeTokens
from ratvision.ui.tooltip import attach_tooltip


class ProfileRow(tk.Frame):
    def __init__(
        self,
        master,
        profile: GameProfile,
        *,
        theme: ThemeTokens,
        selected: bool,
        command,
        toggle_command,
        asset_manager: AssetManager | None = None,
    ):
        super().__init__(
            master,
            background=theme.panel if selected else theme.sidebar,
            highlightthickness=1,
            highlightbackground=theme.text if selected else theme.sidebar,
            bd=0,
            cursor="hand2",
        )
        self.profile = profile
        self.theme = theme
        self.command = command
        self.toggle_command = toggle_command
        self.asset_manager = asset_manager
        semantic_key = self._semantic_key(profile)
        semantic_asset = asset_manager.semantic(semantic_key, 34) if asset_manager else None
        self.emoji_image = semantic_asset.image if semantic_asset else None
        self.emoji_label = tk.Label(
            self,
            text="" if self.emoji_image else profile.emoji,
            image=self.emoji_image or "",
            font=(theme.font_ui[0], 16),
            background=self.cget("background"),
            foreground=theme.text,
        )
        self.emoji_label.grid(row=0, column=0, rowspan=2, padx=(8, 6), pady=8, sticky="n")
        self.name_label = tk.Label(
            self,
            text=profile.name,
            font=(theme.font_ui[0], 9, "bold" if selected else "normal"),
            background=self.cget("background"),
            foreground=theme.text if profile.enabled else theme.text_muted,
            anchor="w",
        )
        self.name_label.grid(row=0, column=1, padx=(0, 6), pady=(7, 0), sticky="ew")
        self.status_label = tk.Label(
            self,
            text="ENABLED" if profile.enabled else "DISABLED",
            font=theme.font_mono,
            background=self.cget("background"),
            foreground=theme.text_muted,
            anchor="w",
        )
        self.status_label.grid(row=1, column=1, padx=(0, 6), pady=(0, 7), sticky="ew")
        self.toggle = RatToggle(
            self,
            value=profile.enabled,
            command=self._toggle,
            theme=theme,
            width=64,
            height=28,
        )
        self.toggle.grid(row=0, column=2, rowspan=2, padx=(4, 8), sticky="e")
        if profile.builtin_id == "global":
            global_help = (
                "Global is the fallback profile used when no enabled game profile matches the active app. "
                "This switch enables only Global; game-profile switches affect only their games, while XRAT TRACING is the master switch for every profile."
            )
            attach_tooltip(self.toggle, global_help, theme)
            attach_tooltip(self.name_label, global_help, theme)
        else:
            attach_tooltip(self.toggle, "Enable or disable this game profile without opening it. XRAT TRACING remains the master switch for all profiles.", theme)
            attach_tooltip(self.name_label, "Open this profile's settings.", theme)
        self.columnconfigure(1, weight=1)
        for widget in (self, self.emoji_label, self.name_label, self.status_label):
            widget.bind("<Button-1>", self._click)

    @staticmethod
    def _semantic_key(profile: GameProfile) -> str:
        if profile.builtin_id == "global":
            return "global"
        name = profile.name.casefold()
        if "arena" in name:
            return "arena"
        if "hunt" in name:
            return "hunt"
        if "tarkov" in name:
            return "rat"
        return "game"

    def _click(self, _event):
        self.command(self.profile.id)

    def _toggle(self, enabled: bool):
        self.profile.enabled = bool(enabled)
        self.name_label.configure(foreground=self.theme.text if enabled else self.theme.text_muted)
        self.status_label.configure(text="ENABLED" if enabled else "DISABLED")
        self.toggle_command(self.profile.id, bool(enabled))


class Sidebar(tk.Frame):
    def __init__(
        self,
        master,
        *,
        profiles: list[GameProfile],
        selected_profile_id: str | None,
        theme: ThemeTokens,
        on_select,
        on_toggle,
        on_add_game,
        on_donate,
        on_settings,
        on_tour=None,
        show_tour_hint: bool = False,
        on_dismiss_tour_hint=None,
    ):
        super().__init__(master, background=theme.sidebar, width=320)
        self.grid_propagate(False)
        self.theme = theme
        self.asset_manager = AssetManager(self.winfo_toplevel())
        self.profile_rows: list[ProfileRow] = []

        title = tk.Label(
            self,
            text="🎮  PROFILES",
            background=theme.sidebar,
            foreground=theme.text,
            font=theme.font_display,
            anchor="w",
        )
        title.grid(row=0, column=0, padx=18, pady=(20, 12), sticky="ew")

        row_index = 1
        self.tour_hint = None
        if show_tour_hint and on_tour is not None:
            hint = tk.Frame(self, background=theme.panel, highlightthickness=1, highlightbackground=theme.border)
            hint.grid(row=row_index, column=0, padx=12, pady=(0, 8), sticky="ew")
            tk.Label(
                hint,
                text="🐀  New here?\nTake the 60-second tour.",
                background=theme.panel,
                foreground=theme.text,
                font=theme.font_small,
                justify="left",
                anchor="w",
            ).pack(side="left", padx=9, pady=7)
            start = tk.Label(hint, text="START", background=theme.panel, foreground=theme.accent, font=theme.font_mono, cursor="hand2")
            start.pack(side="right", padx=(4, 8))
            start.bind("<Button-1>", lambda _e: on_tour())
            close = tk.Label(hint, text="×", background=theme.panel, foreground=theme.text_muted, font=theme.font_ui, cursor="hand2")
            close.pack(side="right")
            if on_dismiss_tour_hint:
                close.bind("<Button-1>", lambda _e: on_dismiss_tour_hint())
            self.tour_hint = hint
            row_index += 1

        list_frame = tk.Frame(self, background=theme.sidebar)
        list_frame.grid(row=row_index, column=0, padx=12, sticky="nsew")
        list_frame.columnconfigure(0, weight=1)
        for idx, profile in enumerate(profiles):
            row = ProfileRow(
                list_frame,
                profile,
                theme=theme,
                selected=profile.id == selected_profile_id,
                command=on_select,
                toggle_command=on_toggle,
                asset_manager=self.asset_manager,
            )
            row.grid(row=idx, column=0, sticky="ew", pady=3)
            self.profile_rows.append(row)
        row_index += 1

        self.add_game_button = RatButton(
            self,
            text="➕  ADD GAME",
            command=on_add_game,
            theme=theme,
            width=284,
            height=38,
        )
        self.add_game_button.grid(row=row_index, column=0, padx=18, pady=(14, 6), sticky="ew")
        attach_tooltip(self.add_game_button, "Create a profile from a running application or an .exe file.", theme)
        row_index += 1

        spacer_row = row_index
        spacer = tk.Frame(self, background=theme.sidebar)
        spacer.grid(row=spacer_row, column=0, sticky="nsew")
        row_index += 1

        # Three long narrow track stripes: a tiny sportswear easter egg.
        self.stripe = tk.Canvas(self, width=52, height=46, background=theme.sidebar, highlightthickness=0)
        for x in (2, 18, 34):
            self.stripe.create_rectangle(x, 2, x + 8, 42, fill=theme.text, outline="", tags=("decorative-stripe",))
        self.stripe.grid(row=row_index, column=0, padx=18, pady=(0, 10), sticky="w")
        attach_tooltip(
            self.stripe,
            "KILLA // ★★★★★\n‘Три полоски есть. RAT VISION одобряю.’",
            theme,
        )
        row_index += 1

        self.donate_button = RatButton(
            self,
            text="☕ Buy me a coffee",
            command=on_donate,
            theme=theme,
            width=284,
            height=38,
        )
        self.donate_button.grid(row=row_index, column=0, padx=18, pady=(0, 8), sticky="ew")
        attach_tooltip(self.donate_button, "Support RAT VISION development with a coffee.", theme)
        row_index += 1
        self.settings_button = RatButton(
            self,
            text="⚙ SETTINGS",
            command=on_settings,
            theme=theme,
            width=284,
            height=38,
        )
        self.settings_button.grid(row=row_index, column=0, padx=18, pady=(0, 18), sticky="ew")
        attach_tooltip(self.settings_button, "Open startup, appearance, diagnostics and update settings.", theme)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(spacer_row, weight=1)
