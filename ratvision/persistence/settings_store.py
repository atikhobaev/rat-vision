from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence

from ratvision.domain.defaults import create_default_profiles, ensure_global_profile
from ratvision.domain.models import (
    AppSettings,
    DisplayInfo,
    GameProfile,
    ThemeMode,
    VisualParameters,
)
from .migration import CURRENT_SCHEMA_VERSION, migrate_payload


class SettingsStore:
    def __init__(self, path: Path):
        self.path = Path(path)

    def load(self, displays: Sequence[DisplayInfo]) -> AppSettings:
        if not self.path.exists():
            return self._defaults(displays)
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError, UnicodeError):
            self._backup_invalid()
            return self._defaults(displays)
        try:
            return self._from_payload(migrate_payload(payload), displays)
        except (TypeError, ValueError, KeyError):
            self._backup_invalid()
            return self._defaults(displays)

    def save(self, settings: AppSettings) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(self.path.suffix + ".tmp")
        tmp.write_text(
            json.dumps(self._to_payload(settings), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        tmp.replace(self.path)

    def export_to(self, settings: AppSettings, destination: Path) -> None:
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            json.dumps(self._to_payload(settings, include_local_state=False), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def import_from(self, source: Path, displays: Sequence[DisplayInfo]) -> AppSettings:
        payload = json.loads(Path(source).read_text(encoding="utf-8"))
        return self._from_payload(migrate_payload(payload), displays)

    def _backup_invalid(self) -> None:
        if not self.path.exists():
            return
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        target = self.path.with_name(f"settings.invalid-{stamp}{self.path.suffix}")
        counter = 1
        while target.exists():
            target = self.path.with_name(f"settings.invalid-{stamp}-{counter}{self.path.suffix}")
            counter += 1
        try:
            self.path.replace(target)
        except OSError:
            pass

    @staticmethod
    def _defaults(displays: Sequence[DisplayInfo]) -> AppSettings:
        return AppSettings(profiles=create_default_profiles(displays))

    @staticmethod
    def _to_payload(settings: AppSettings, *, include_local_state: bool = True) -> dict[str, Any]:
        app = {
                "global_enabled": settings.global_enabled,
                "theme": settings.theme.value,
                "launch_with_windows": settings.launch_with_windows,
                "start_minimized": settings.start_minimized,
                "close_to_tray": settings.close_to_tray,
                "always_on_top": settings.always_on_top,
                "tour_prompt_seen": settings.tour_prompt_seen,
            }
        if include_local_state:
            app.update({
                "analytics_enabled": settings.analytics_enabled,
                "analytics_install_id": settings.analytics_install_id,
                "analytics_last_daily_active": settings.analytics_last_daily_active,
            })
        return {
            "schema_version": CURRENT_SCHEMA_VERSION,
            "app": app,
            "profiles": [
                {
                    "id": profile.id,
                    "name": profile.name,
                    "emoji": profile.emoji,
                    "enabled": profile.enabled,
                    "processes": list(profile.processes),
                    "display_ids": list(profile.display_ids),
                    "visual": {
                        "brightness": profile.visual.brightness,
                        "contrast": profile.visual.contrast,
                        "gamma": profile.visual.gamma,
                        "saturation": profile.visual.saturation,
                    },
                    "builtin_id": profile.builtin_id,
                }
                for profile in settings.profiles
            ],
        }

    @staticmethod
    def _from_payload(payload: dict[str, Any], displays: Sequence[DisplayInfo]) -> AppSettings:
        app = payload.get("app") or {}
        profile_rows = payload.get("profiles") or []
        profiles: list[GameProfile] = []
        for row in profile_rows:
            visual = row.get("visual") or {}
            profiles.append(
                GameProfile(
                    id=str(row.get("id") or ""),
                    name=str(row.get("name") or "Game"),
                    emoji=str(row.get("emoji") or "🎮"),
                    enabled=bool(row.get("enabled", True)),
                    processes=[str(v) for v in row.get("processes") or []],
                    display_ids=[str(v) for v in row.get("display_ids") or []],
                    visual=VisualParameters(
                        float(visual.get("brightness", 0.5)),
                        float(visual.get("contrast", 0.5)),
                        float(visual.get("gamma", 1.0)),
                        int(visual.get("saturation", 0)),
                    ),
                    builtin_id=row.get("builtin_id"),
                )
            )
        if not profiles:
            profiles = create_default_profiles(displays)
        else:
            ensure_global_profile(profiles, displays)
        try:
            theme = ThemeMode(str(app.get("theme", ThemeMode.NIGHT.value)))
        except ValueError:
            theme = ThemeMode.NIGHT
        return AppSettings(
            schema_version=CURRENT_SCHEMA_VERSION,
            global_enabled=bool(app.get("global_enabled", True)),
            theme=theme,
            profiles=profiles,
            launch_with_windows=bool(app.get("launch_with_windows", False)),
            start_minimized=bool(app.get("start_minimized", False)),
            close_to_tray=bool(app.get("close_to_tray", True)),
            always_on_top=bool(app.get("always_on_top", False)),
            tour_prompt_seen=bool(app.get("tour_prompt_seen", False)),
            analytics_enabled=bool(app.get("analytics_enabled", True)),
            analytics_install_id=(str(app.get("analytics_install_id")) if app.get("analytics_install_id") else None),
            analytics_last_daily_active=(float(app.get("analytics_last_daily_active")) if app.get("analytics_last_daily_active") is not None else None),
        )
