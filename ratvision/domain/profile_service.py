from __future__ import annotations

from ratvision.domain.models import AppSettings, GameProfile, VisualParameters, normalize_executable


class ProfileService:
    def __init__(self, settings: AppSettings):
        self.settings = settings

    @property
    def profiles(self) -> list[GameProfile]:
        return self.settings.profiles

    def get(self, profile_id: str) -> GameProfile:
        for profile in self.profiles:
            if profile.id == profile_id:
                return profile
        raise KeyError(profile_id)

    def match(self, executable: str) -> GameProfile | None:
        identity = normalize_executable(executable)
        for profile in self.profiles:
            if profile.enabled and identity in profile.processes:
                return profile
        return None

    def global_profile(self) -> GameProfile | None:
        for profile in self.profiles:
            if profile.builtin_id == "global":
                return profile
        return None

    def copy_visuals(self, source_id: str, target_id: str) -> None:
        source = self.get(source_id)
        target = self.get(target_id)
        target.visual = VisualParameters(
            source.visual.brightness,
            source.visual.contrast,
            source.visual.gamma,
            source.visual.saturation,
        )

    def add_process(self, profile_id: str, executable: str) -> None:
        profile = self.get(profile_id)
        if profile.builtin_id == "global":
            raise ValueError("Global profile is process-independent")
        identity = normalize_executable(executable)
        if identity and identity not in profile.processes:
            profile.processes.append(identity)

    def remove_process(self, profile_id: str, executable: str) -> None:
        profile = self.get(profile_id)
        identity = normalize_executable(executable)
        profile.processes = [value for value in profile.processes if value != identity]

    def set_displays(self, profile_id: str, display_ids: list[str]) -> None:
        self.get(profile_id).display_ids = list(dict.fromkeys(display_ids))

    def add_profile(self, profile: GameProfile) -> None:
        self.settings.profiles.append(profile)

    def remove_profile(self, profile_id: str) -> GameProfile:
        profile = self.get(profile_id)
        if profile.builtin_id == "global":
            raise ValueError("Global profile cannot be removed")
        self.settings.profiles.remove(profile)
        return profile
