from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from collections.abc import Callable, Iterable

import psutil

from ratvision.domain.models import normalize_executable


@dataclass(frozen=True, slots=True)
class RunningProcess:
    pid: int
    executable: str
    friendly_name: str
    path: str | None = None


class ProcessDiscovery:
    def __init__(self, process_iter: Callable[[], Iterable] | None = None):
        self._process_iter = process_iter or (lambda: psutil.process_iter(["pid", "name", "exe"]))

    def list_running(self) -> list[RunningProcess]:
        found: dict[str, RunningProcess] = {}
        try:
            rows = self._process_iter()
        except (psutil.Error, OSError):
            return []
        for proc in rows:
            try:
                info = proc.info
                raw_name = str(info.get("name") or "").strip()
                raw_path = info.get("exe")
                identity = normalize_executable(str(raw_path or raw_name))
                if not identity:
                    continue
                friendly = Path(raw_name).stem if raw_name else (Path(str(raw_path)).stem if raw_path else Path(identity).stem)
                item = RunningProcess(
                    pid=int(info.get("pid") or 0),
                    executable=identity,
                    friendly_name=friendly,
                    path=str(raw_path) if raw_path else None,
                )
                found.setdefault(identity, item)
            except (psutil.AccessDenied, psutil.NoSuchProcess, psutil.ZombieProcess, OSError, ValueError, TypeError):
                continue
        return list(found.values())
