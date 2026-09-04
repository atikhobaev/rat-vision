from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from ratvision.domain.models import DisplayInfo, ForegroundProcess, VisualParameters, normalize_executable
from .base import ForegroundCallback


class SimulationForegroundProvider:
    def __init__(self) -> None:
        self._callback: ForegroundCallback | None = None
        self._current = ForegroundProcess(0, "", "")

    def start(self, callback: ForegroundCallback) -> None:
        self._callback = callback

    def stop(self) -> None:
        self._callback = None

    def current(self) -> ForegroundProcess:
        return self._current

    def focus(self, executable: str, *, pid: int = 1000, title: str = "") -> None:
        self._current = ForegroundProcess(pid, normalize_executable(executable), title)
        if self._callback is not None:
            self._callback(self._current)


class SimulationDisplayProvider:
    def __init__(self, displays: Iterable[DisplayInfo] | None = None) -> None:
        self._displays = list(displays or [])

    def list_displays(self) -> list[DisplayInfo]:
        return list(self._displays)

    def set_displays(self, displays: Iterable[DisplayInfo]) -> None:
        self._displays = list(displays)


class SimulationColorBackend:
    def __init__(self) -> None:
        self.captured: set[str] = set()
        self.applied: list[tuple[str, VisualParameters]] = []
        self.restored: list[str] = []
        self.restore_all_count = 0

    def capture(self, display_id: str) -> None:
        self.captured.add(display_id)

    def apply(self, display_id: str, params: VisualParameters) -> None:
        self.applied.append((display_id, params.normalized()))

    def restore(self, display_id: str) -> None:
        self.restored.append(display_id)

    def restore_all(self) -> None:
        self.restore_all_count += 1
        for display_id in sorted(self.captured):
            self.restore(display_id)

    def capabilities(self, display_id: str) -> dict[str, Any]:
        return {
            "display_id": display_id,
            "brightness": True,
            "contrast": True,
            "gamma": True,
            "saturation": True,
            "simulated": True,
        }


class SimulationTrayBackend:
    def __init__(self) -> None:
        self.running = False
        self.enabled = False
        self.actions: Any = None

    def start(self, actions: Any) -> None:
        self.actions = actions
        self.running = True

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = bool(enabled)

    def stop(self) -> None:
        self.running = False


class SimulationStartupBackend:
    def __init__(self, enabled: bool = False) -> None:
        self._enabled = enabled

    def is_enabled(self) -> bool:
        return self._enabled

    def set_enabled(self, value: bool) -> None:
        self._enabled = bool(value)
