from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from collections.abc import Callable

from ratvision.platform.windows.nvapi import NvApiNative


class DvcHelperError(RuntimeError):
    pass


def execute_dvc_helper_operation(operation: str, display_id: str, level: int | None, *, native=None) -> dict[str, int]:
    native = native or NvApiNative()
    initialized = False
    try:
        native.initialize()
        initialized = True
        handle = native.get_display_handle(display_id)
        if operation == "capture":
            info = native.get_dvc_info(handle)
            return {"current": int(info.current), "minimum": int(info.minimum), "maximum": int(info.maximum)}
        if operation == "set":
            if level is None:
                raise ValueError("level is required for set")
            native.set_dvc_level(handle, int(level))
            return {"level": int(level)}
        raise ValueError(f"unsupported DVC helper operation: {operation}")
    finally:
        if initialized:
            try:
                native.unload()
            except Exception:
                pass


def build_dvc_helper_command(
    executable: str,
    *,
    frozen: bool,
    operation: str,
    display_id: str,
    level: int | None = None,
    result_file: Path | None = None,
) -> list[str]:
    if frozen:
        command = [executable, "--dvc-helper", operation, "--display", display_id]
    else:
        command = [executable, "-m", "ratvision.platform.windows.dvc_helper", operation, "--display", display_id]
    if level is not None:
        command.extend(["--level", str(int(level))])
    if result_file is not None:
        command.extend(["--result-file", str(result_file)])
    return command


class DvcSubprocessController:
    """Run every private NVAPI DVC operation in a disposable child process.

    A driver/private-NVAPI access violation can terminate the helper without
    taking the Tk application down with it.
    """

    def __init__(
        self,
        *,
        runner: Callable[..., object] | None = None,
        executable: str | None = None,
        frozen: bool | None = None,
        timeout: float = 5.0,
        log_path: Path | None = None,
        temp_dir: Path | None = None,
    ) -> None:
        self.runner = runner or subprocess.run
        self.executable = executable or sys.executable
        self.frozen = bool(getattr(sys, "frozen", False)) if frozen is None else bool(frozen)
        self.timeout = float(timeout)
        self.log_path = Path(log_path) if log_path is not None else None
        self.temp_dir = Path(temp_dir) if temp_dir is not None else None
        self.originals: dict[str, int] = {}
        self.ranges: dict[str, tuple[int, int]] = {}

    def _log(self, message: str) -> None:
        if self.log_path is None:
            return
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        with self.log_path.open("a", encoding="utf-8") as handle:
            handle.write(message.rstrip() + "\n")

    def _invoke(self, operation: str, display_id: str, level: int | None = None) -> dict[str, int]:
        fd, raw_path = tempfile.mkstemp(prefix="ratvision-dvc-", suffix=".json", dir=self.temp_dir)
        os.close(fd)
        result_path = Path(raw_path)
        try:
            result_path.unlink(missing_ok=True)
            command = build_dvc_helper_command(
                self.executable,
                frozen=self.frozen,
                operation=operation,
                display_id=display_id,
                level=level,
                result_file=result_path,
            )
            kwargs: dict[str, object] = {
                "capture_output": True,
                "text": True,
                "timeout": self.timeout,
                "check": False,
            }
            if os.name == "nt":
                kwargs["creationflags"] = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            self._log(f"> {operation} {display_id}" + (f" level={level}" if level is not None else ""))
            try:
                completed = self.runner(command, **kwargs)
            except Exception as exc:
                self._log(f"! helper launch failed: {exc!r}")
                raise DvcHelperError(f"DVC helper launch failed: {exc}") from exc

            returncode = int(getattr(completed, "returncode", 1))
            stdout = str(getattr(completed, "stdout", "") or "").strip()
            stderr = str(getattr(completed, "stderr", "") or "").strip()
            if returncode != 0:
                self._log(f"! helper exited {returncode}; stderr={stderr!r}; stdout={stdout!r}")
                raise DvcHelperError(f"DVC helper exited with code {returncode}")
            if not result_path.exists():
                self._log(f"! helper returned no result file; stderr={stderr!r}; stdout={stdout!r}")
                raise DvcHelperError("DVC helper returned no result file")
            try:
                payload = json.loads(result_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                self._log(f"! invalid helper result file; stderr={stderr!r}; stdout={stdout!r}")
                raise DvcHelperError("DVC helper returned invalid JSON") from exc
            if not payload.get("ok"):
                error = str(payload.get("error", "unknown DVC helper error"))
                self._log(f"! helper error: {error}")
                raise DvcHelperError(error)
            result = payload.get("result") or {}
            self._log(f"< ok {result}")
            return {str(key): int(value) for key, value in result.items()}
        finally:
            result_path.unlink(missing_ok=True)

    def capture(self, display_id: str) -> None:
        if display_id in self.originals:
            return
        result = self._invoke("capture", display_id)
        self.originals[display_id] = int(result["current"])
        self.ranges[display_id] = (int(result["minimum"]), int(result["maximum"]))

    def set_level(self, display_id: str, level: int) -> None:
        self.capture(display_id)
        minimum, maximum = self.ranges[display_id]
        clamped = min(max(int(level), minimum), maximum)
        self._invoke("set", display_id, clamped)

    def restore(self, display_id: str) -> None:
        if display_id in self.originals:
            self._invoke("set", display_id, self.originals[display_id])

    def restore_all(self) -> None:
        for display_id in list(self.originals):
            try:
                self.restore(display_id)
            except Exception:
                pass

    def capabilities(self, display_id: str) -> dict[str, object]:
        try:
            self.capture(display_id)
        except Exception as exc:
            return {"supported": False, "reason": str(exc)}
        minimum, maximum = self.ranges[display_id]
        return {"supported": True, "minimum": minimum, "maximum": maximum}
