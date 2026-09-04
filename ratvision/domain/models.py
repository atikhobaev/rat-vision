from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from uuid import uuid4


class ThemeMode(str, Enum):
    NIGHT = "night"
    DAY = "day"
    SYSTEM = "system"


@dataclass(frozen=True, slots=True)
class VisualParameters:
    brightness: float = 0.5
    contrast: float = 0.5
    gamma: float = 1.0
    saturation: int = 0

    def normalized(self) -> "VisualParameters":
        return VisualParameters(
            brightness=min(max(float(self.brightness), 0.0), 1.0),
            contrast=min(max(float(self.contrast), 0.0), 1.0),
            gamma=min(max(float(self.gamma), 0.4), 2.8),
            saturation=int(min(max(int(self.saturation), 0), 100)),
        )


@dataclass(frozen=True, slots=True)
class DisplayInfo:
    id: str
    name: str
    width: int
    height: int
    refresh_hz: float | None
    primary: bool
    online: bool


@dataclass(frozen=True, slots=True)
class ForegroundProcess:
    pid: int
    executable: str
    title: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "executable", self.executable.strip().lower())


@dataclass(slots=True)
class GameProfile:
    id: str = field(default_factory=lambda: str(uuid4()))
    name: str = "Game"
    emoji: str = "🎮"
    enabled: bool = True
    processes: list[str] = field(default_factory=list)
    display_ids: list[str] = field(default_factory=list)
    visual: VisualParameters = field(default_factory=VisualParameters)
    builtin_id: str | None = None

    def __post_init__(self) -> None:
        self.processes = _normalize_processes(self.processes)
        self.display_ids = list(dict.fromkeys(self.display_ids))
        self.visual = self.visual.normalized()


@dataclass(slots=True)
class AppSettings:
    schema_version: int = 1
    global_enabled: bool = True
    theme: ThemeMode = ThemeMode.NIGHT
    profiles: list[GameProfile] = field(default_factory=list)
    launch_with_windows: bool = False
    start_minimized: bool = False
    close_to_tray: bool = True
    always_on_top: bool = False
    tour_prompt_seen: bool = False
    analytics_enabled: bool = True
    analytics_install_id: str | None = None
    analytics_last_daily_active: float | None = None


def normalize_executable(value: str) -> str:
    value = value.strip().replace("\\", "/").split("/")[-1].lower()
    return value


def _normalize_processes(values: list[str]) -> list[str]:
    normalized = [normalize_executable(value) for value in values if value and value.strip()]
    return list(dict.fromkeys(normalized))
