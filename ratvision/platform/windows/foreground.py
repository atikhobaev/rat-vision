from __future__ import annotations

import ctypes
from ctypes import wintypes
import sys
from collections.abc import Callable

import psutil

from ratvision.domain.models import ForegroundProcess, normalize_executable
from ratvision.platform.base import ForegroundCallback, PlatformUnavailableError

EVENT_SYSTEM_FOREGROUND = 0x0003
WINEVENT_OUTOFCONTEXT = 0x0000
WINEVENT_SKIPOWNPROCESS = 0x0002

_WINEVENTPROC_FACTORY = getattr(ctypes, "WINFUNCTYPE", ctypes.CFUNCTYPE)
_WINEVENTPROC = _WINEVENTPROC_FACTORY(
    None,
    wintypes.HANDLE,
    wintypes.DWORD,
    wintypes.HWND,
    wintypes.LONG,
    wintypes.LONG,
    wintypes.DWORD,
    wintypes.DWORD,
)


def configure_user32_signatures(user32) -> None:
    """Configure Win32 prototypes so 64-bit handles are never truncated by ctypes."""
    user32.SetWinEventHook.argtypes = [
        wintypes.DWORD, wintypes.DWORD, wintypes.HMODULE, _WINEVENTPROC,
        wintypes.DWORD, wintypes.DWORD, wintypes.DWORD,
    ]
    user32.SetWinEventHook.restype = wintypes.HANDLE
    user32.UnhookWinEvent.argtypes = [wintypes.HANDLE]
    user32.UnhookWinEvent.restype = wintypes.BOOL
    user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    user32.GetWindowThreadProcessId.restype = wintypes.DWORD
    user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    user32.GetWindowTextLengthW.restype = ctypes.c_int
    user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    user32.GetWindowTextW.restype = ctypes.c_int


class WindowsForegroundProvider:
    def __init__(self, *, user32=None, resolver: Callable[[int], ForegroundProcess] | None = None, callback_factory=None):
        if user32 is None:
            if sys.platform != "win32":
                raise PlatformUnavailableError("Windows foreground hooks require Windows")
            user32 = ctypes.WinDLL("user32", use_last_error=True)
        self.user32 = user32
        try:
            configure_user32_signatures(self.user32)
        except (AttributeError, TypeError):
            # Lightweight test doubles may expose plain bound methods rather than ctypes functions.
            pass
        self._resolver = resolver or self._resolve_hwnd
        self._callback_factory = callback_factory or self._make_native_callback
        self._callback: ForegroundCallback | None = None
        self._native_callback = None
        self._hook = None
        self._current = ForegroundProcess(0, "", "")

    def start(self, callback: ForegroundCallback) -> None:
        if self._hook:
            return
        self._callback = callback

        def on_event(_hook, event_type, hwnd, _id_object, _id_child, _thread, _time):
            if int(event_type) != EVENT_SYSTEM_FOREGROUND:
                return
            try:
                process = self._resolver(int(hwnd or 0))
            except Exception:
                return
            self._current = process
            if self._callback:
                self._callback(process)

        self._native_callback = self._callback_factory(on_event)
        self._hook = self.user32.SetWinEventHook(
            EVENT_SYSTEM_FOREGROUND,
            EVENT_SYSTEM_FOREGROUND,
            None,
            self._native_callback,
            0,
            0,
            WINEVENT_OUTOFCONTEXT | WINEVENT_SKIPOWNPROCESS,
        )
        if not self._hook:
            self._native_callback = None
            raise OSError(ctypes.get_last_error(), "SetWinEventHook failed")

    def stop(self) -> None:
        if self._hook:
            self.user32.UnhookWinEvent(self._hook)
        self._hook = None
        self._native_callback = None
        self._callback = None

    def current(self) -> ForegroundProcess:
        return self._current

    @staticmethod
    def _make_native_callback(callback):
        return _WINEVENTPROC(callback)

    def _resolve_hwnd(self, hwnd: int) -> ForegroundProcess:
        pid = wintypes.DWORD()
        self.user32.GetWindowThreadProcessId(wintypes.HWND(hwnd), ctypes.byref(pid))
        if not pid.value:
            return ForegroundProcess(0, "", "")
        try:
            proc = psutil.Process(pid.value)
            executable = normalize_executable(proc.exe() or proc.name())
        except (psutil.Error, OSError):
            executable = ""
        title = ""
        try:
            length = int(self.user32.GetWindowTextLengthW(wintypes.HWND(hwnd)))
            if length:
                buffer = ctypes.create_unicode_buffer(length + 1)
                self.user32.GetWindowTextW(wintypes.HWND(hwnd), buffer, len(buffer))
                title = buffer.value
        except Exception:
            pass
        return ForegroundProcess(int(pid.value), executable, title)
