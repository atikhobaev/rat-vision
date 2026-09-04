from __future__ import annotations

from collections.abc import Callable

from ratvision.domain.models import AppSettings, DisplayInfo, ForegroundProcess, GameProfile
from ratvision.domain.profile_service import ProfileService
from ratvision.platform.base import ColorBackend


class ActivationCoordinator:
    def __init__(
        self,
        settings: AppSettings,
        profiles: ProfileService,
        color_backend: ColorBackend,
        display_lookup: Callable[[], dict[str, DisplayInfo]],
    ) -> None:
        self.settings = settings
        self.profiles = profiles
        self.color_backend = color_backend
        self.display_lookup = display_lookup
        self.active_profile_id: str | None = None
        self.current_process = ForegroundProcess(0, "", "")

    def set_global_enabled(self, value: bool) -> None:
        value = bool(value)
        if self.settings.global_enabled == value:
            return
        self.settings.global_enabled = value
        if not value:
            self.color_backend.restore_all()
            self.active_profile_id = None
        else:
            self.on_foreground(self.current_process)

    def on_foreground(self, process: ForegroundProcess) -> None:
        self.current_process = process
        if not self.settings.global_enabled:
            return
        matched = self.profiles.match(process.executable)
        if matched is None:
            global_profile = self.profiles.global_profile()
            matched = global_profile if global_profile is not None and global_profile.enabled else None
        if matched is None:
            self._restore_active_profile()
            return
        if self.active_profile_id != matched.id:
            self._restore_active_profile()
        self._apply_profile(matched)
        self.active_profile_id = matched.id

    def refresh_profile(self, profile_id: str) -> None:
        if not self.settings.global_enabled or self.active_profile_id != profile_id:
            return
        self.on_foreground(self.current_process)

    def _apply_profile(self, profile: GameProfile) -> None:
        displays = self.display_lookup()
        for display_id in profile.display_ids:
            display = displays.get(display_id)
            if display is None or not display.online:
                continue
            self.color_backend.capture(display_id)
            self.color_backend.apply(display_id, profile.visual)

    def _restore_active_profile(self) -> None:
        if self.active_profile_id is None:
            return
        try:
            profile = self.profiles.get(self.active_profile_id)
        except KeyError:
            self.color_backend.restore_all()
        else:
            for display_id in profile.display_ids:
                self.color_backend.restore(display_id)
        self.active_profile_id = None
