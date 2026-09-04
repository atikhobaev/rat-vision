from __future__ import annotations

import sys

from ratvision.platform.base import PlatformUnavailableError

try:
    import winreg as _winreg
except ImportError:  # non-Windows
    _winreg = None

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "RAT VISION"


class WindowsStartupBackend:
    def __init__(self, *, command: str, registry=None):
        self.command = command
        self.registry = registry or _winreg
        if self.registry is None:
            raise PlatformUnavailableError("Windows startup registration requires Windows")

    def is_enabled(self) -> bool:
        try:
            with self.registry.OpenKey(self.registry.HKEY_CURRENT_USER, RUN_KEY, 0, self.registry.KEY_READ) as key:
                value, _kind = self.registry.QueryValueEx(key, VALUE_NAME)
            return str(value) == self.command
        except FileNotFoundError:
            return False

    def set_enabled(self, value: bool) -> None:
        with self.registry.OpenKey(self.registry.HKEY_CURRENT_USER, RUN_KEY, 0, self.registry.KEY_SET_VALUE) as key:
            if value:
                self.registry.SetValueEx(key, VALUE_NAME, 0, self.registry.REG_SZ, self.command)
            else:
                try:
                    self.registry.DeleteValue(key, VALUE_NAME)
                except FileNotFoundError:
                    pass
