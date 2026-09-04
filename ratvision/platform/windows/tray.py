from __future__ import annotations

import ctypes
from ctypes import wintypes
from dataclasses import dataclass
from pathlib import Path
import queue
import sys
import tempfile
import threading
from collections.abc import Callable

from PIL import Image

from ratvision import __version__
from ratvision.platform.base import PlatformUnavailableError
from ratvision.ui.tray_assets import render_tray_icon


@dataclass(frozen=True, slots=True)
class TrayActions:
    open_app: Callable[[], None]
    toggle_enabled: Callable[[], None]
    open_settings: Callable[[], None]
    donate: Callable[[], None]
    exit_app: Callable[[], None]


@dataclass(frozen=True, slots=True)
class TrayMenuItem:
    label: str
    action: Callable[[], None] | None


class WindowsTrayBackend:
    def __init__(self, *, shell=None):
        self.shell = shell
        if self.shell is None:
            if sys.platform != "win32":
                raise PlatformUnavailableError("Windows tray requires Windows")
            self.shell = _Win32TrayShell()
        self.actions: TrayActions | None = None
        self.enabled = False
        self.running = False

    def start(self, actions: TrayActions) -> None:
        self.actions = actions
        items = [
            TrayMenuItem(f"RAT VISION v{__version__}", None),
            TrayMenuItem("XRAT TRACING", actions.toggle_enabled),
            TrayMenuItem("Open RAT VISION", actions.open_app),
            TrayMenuItem("Settings", actions.open_settings),
            TrayMenuItem("Buy me a coffee", actions.donate),
            TrayMenuItem("Exit", actions.exit_app),
        ]
        self.shell.add(
            render_tray_icon(False),
            f"RAT VISION // XRAT DISABLED",
            items,
            default_action=actions.open_app,
        )
        self.running = True

    def set_enabled(self, enabled: bool) -> None:
        self.enabled = bool(enabled)
        tooltip = f"RAT VISION // XRAT {'ENABLED' if self.enabled else 'DISABLED'}"
        self.shell.update(render_tray_icon(self.enabled), tooltip)

    def stop(self) -> None:
        if self.running:
            self.shell.remove()
        self.running = False


# The native shell below is intentionally private. The application only relies on
# WindowsTrayBackend, which is fakeable and fully exercised in Linux tests.
NIM_ADD = 0x00000000
NIM_MODIFY = 0x00000001
NIM_DELETE = 0x00000002
NIF_MESSAGE = 0x00000001
NIF_ICON = 0x00000002
NIF_TIP = 0x00000004
WM_APP = 0x8000
TRAY_MESSAGE = WM_APP + 77
WM_LBUTTONUP = 0x0202
WM_RBUTTONUP = 0x0205
WM_CONTEXTMENU = 0x007B
WM_CLOSE = 0x0010
WM_DESTROY = 0x0002
TPM_RETURNCMD = 0x0100
TPM_NONOTIFY = 0x0080
MF_STRING = 0x0000
MF_GRAYED = 0x0001
IMAGE_ICON = 1
LR_LOADFROMFILE = 0x0010


class GUID(ctypes.Structure):
    _fields_ = [("Data1", wintypes.DWORD), ("Data2", wintypes.WORD), ("Data3", wintypes.WORD), ("Data4", ctypes.c_ubyte * 8)]


class NOTIFYICONDATAW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("hWnd", wintypes.HWND),
        ("uID", wintypes.UINT),
        ("uFlags", wintypes.UINT),
        ("uCallbackMessage", wintypes.UINT),
        ("hIcon", wintypes.HICON),
        ("szTip", wintypes.WCHAR * 128),
        ("dwState", wintypes.DWORD),
        ("dwStateMask", wintypes.DWORD),
        ("szInfo", wintypes.WCHAR * 256),
        ("uTimeoutOrVersion", wintypes.UINT),
        ("szInfoTitle", wintypes.WCHAR * 64),
        ("dwInfoFlags", wintypes.DWORD),
        ("guidItem", GUID),
        ("hBalloonIcon", wintypes.HICON),
    ]


class WNDCLASSW(ctypes.Structure):
    pass


_WNDPROC = getattr(ctypes, "WINFUNCTYPE", ctypes.CFUNCTYPE)(
    wintypes.LPARAM,
    wintypes.HWND,
    wintypes.UINT,
    wintypes.WPARAM,
    wintypes.LPARAM,
)

WNDCLASSW._fields_ = [
    ("style", wintypes.UINT),
    ("lpfnWndProc", _WNDPROC),
    ("cbClsExtra", ctypes.c_int),
    ("cbWndExtra", ctypes.c_int),
    ("hInstance", wintypes.HINSTANCE),
    ("hIcon", wintypes.HICON),
    ("hCursor", wintypes.HANDLE),
    ("hbrBackground", wintypes.HBRUSH),
    ("lpszMenuName", wintypes.LPCWSTR),
    ("lpszClassName", wintypes.LPCWSTR),
]


class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]


def configure_tray_signatures(user32, shell32, kernel32) -> None:
    """Assign pointer-safe ctypes signatures for all tray Win32 calls."""
    kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
    kernel32.GetModuleHandleW.restype = wintypes.HMODULE

    shell32.Shell_NotifyIconW.argtypes = [wintypes.DWORD, ctypes.POINTER(NOTIFYICONDATAW)]
    shell32.Shell_NotifyIconW.restype = wintypes.BOOL

    user32.PostMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.PostMessageW.restype = wintypes.BOOL
    user32.DestroyIcon.argtypes = [wintypes.HICON]
    user32.DestroyIcon.restype = wintypes.BOOL
    user32.LoadImageW.argtypes = [wintypes.HINSTANCE, wintypes.LPCWSTR, wintypes.UINT, ctypes.c_int, ctypes.c_int, wintypes.UINT]
    user32.LoadImageW.restype = wintypes.HANDLE
    user32.CreatePopupMenu.argtypes = []
    user32.CreatePopupMenu.restype = wintypes.HMENU
    user32.AppendMenuW.argtypes = [wintypes.HMENU, wintypes.UINT, ctypes.c_size_t, wintypes.LPCWSTR]
    user32.AppendMenuW.restype = wintypes.BOOL
    user32.GetCursorPos.argtypes = [ctypes.POINTER(POINT)]
    user32.GetCursorPos.restype = wintypes.BOOL
    user32.SetForegroundWindow.argtypes = [wintypes.HWND]
    user32.SetForegroundWindow.restype = wintypes.BOOL
    user32.TrackPopupMenu.argtypes = [wintypes.HMENU, wintypes.UINT, ctypes.c_int, ctypes.c_int, ctypes.c_int, wintypes.HWND, wintypes.LPVOID]
    user32.TrackPopupMenu.restype = wintypes.UINT
    user32.DestroyMenu.argtypes = [wintypes.HMENU]
    user32.DestroyMenu.restype = wintypes.BOOL
    user32.RegisterClassW.argtypes = [ctypes.POINTER(WNDCLASSW)]
    user32.RegisterClassW.restype = wintypes.ATOM
    user32.CreateWindowExW.argtypes = [
        wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
        ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
        wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID,
    ]
    user32.CreateWindowExW.restype = wintypes.HWND
    user32.GetMessageW.argtypes = [ctypes.POINTER(wintypes.MSG), wintypes.HWND, wintypes.UINT, wintypes.UINT]
    user32.GetMessageW.restype = ctypes.c_int
    user32.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
    user32.TranslateMessage.restype = wintypes.BOOL
    user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
    user32.DispatchMessageW.restype = wintypes.LPARAM
    user32.DefWindowProcW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
    user32.DefWindowProcW.restype = wintypes.LPARAM


class _Win32TrayShell:
    def __init__(self):
        self.user32 = ctypes.WinDLL("user32", use_last_error=True)
        self.shell32 = ctypes.WinDLL("shell32", use_last_error=True)
        self.kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        configure_tray_signatures(self.user32, self.shell32, self.kernel32)
        self._hwnd = None
        self._icon = None
        self._menu_items: list[TrayMenuItem] = []
        self._ready = threading.Event()
        self._thread: threading.Thread | None = None
        self._wndproc = None
        self._tmp = tempfile.TemporaryDirectory(prefix="ratvision-tray-")
        self._commands: queue.Queue[tuple[str, object]] = queue.Queue()
        self._default_action: Callable[[], None] | None = None

    def add(
        self,
        icon: Image.Image,
        tooltip: str,
        menu_items: list[TrayMenuItem],
        *,
        default_action: Callable[[], None] | None = None,
    ) -> None:
        self._menu_items = list(menu_items)
        self._default_action = default_action
        self._thread = threading.Thread(target=self._message_loop, name="RatVisionTray", daemon=True)
        self._thread.start()
        if not self._ready.wait(3.0):
            raise RuntimeError("Tray window did not initialize")
        self._apply_icon(NIM_ADD, icon, tooltip)

    def update(self, icon: Image.Image, tooltip: str) -> None:
        if self._hwnd:
            self._apply_icon(NIM_MODIFY, icon, tooltip)

    def remove(self) -> None:
        if self._hwnd:
            data = self._data(None, "")
            self.shell32.Shell_NotifyIconW(NIM_DELETE, ctypes.byref(data))
            self.user32.PostMessageW(self._hwnd, WM_CLOSE, 0, 0)
        if self._thread:
            self._thread.join(timeout=2.0)
        if self._icon:
            self.user32.DestroyIcon(self._icon)
            self._icon = None
        self._tmp.cleanup()

    def _icon_file(self, image: Image.Image) -> Path:
        path = Path(self._tmp.name) / "tray.ico"
        image.save(path, format="ICO", sizes=[(16, 16), (20, 20), (24, 24), (32, 32), (48, 48)])
        return path

    def _load_icon(self, image: Image.Image):
        path = self._icon_file(image)
        hicon = self.user32.LoadImageW(None, str(path), IMAGE_ICON, 0, 0, LR_LOADFROMFILE)
        if not hicon:
            raise OSError(ctypes.get_last_error(), "LoadImageW tray icon failed")
        return hicon

    def _data(self, hicon, tooltip: str):
        data = NOTIFYICONDATAW()
        data.cbSize = ctypes.sizeof(data)
        data.hWnd = self._hwnd
        data.uID = 1
        data.uFlags = NIF_MESSAGE | NIF_TIP | (NIF_ICON if hicon else 0)
        data.uCallbackMessage = TRAY_MESSAGE
        data.hIcon = hicon or None
        data.szTip = tooltip[:127]
        return data

    def _apply_icon(self, op: int, image: Image.Image, tooltip: str) -> None:
        new_icon = self._load_icon(image)
        data = self._data(new_icon, tooltip)
        if not self.shell32.Shell_NotifyIconW(op, ctypes.byref(data)):
            self.user32.DestroyIcon(new_icon)
            raise OSError(ctypes.get_last_error(), "Shell_NotifyIconW failed")
        old_icon, self._icon = self._icon, new_icon
        if old_icon:
            self.user32.DestroyIcon(old_icon)

    def _show_menu(self):
        menu = self.user32.CreatePopupMenu()
        command_map: dict[int, Callable[[], None]] = {}
        command_id = 100
        for item in self._menu_items:
            flags = MF_STRING
            if item.action is None:
                flags |= MF_GRAYED
            self.user32.AppendMenuW(menu, flags, command_id, item.label)
            if item.action is not None:
                command_map[command_id] = item.action
            command_id += 1
        point = POINT()
        self.user32.GetCursorPos(ctypes.byref(point))
        self.user32.SetForegroundWindow(self._hwnd)
        chosen = self.user32.TrackPopupMenu(menu, TPM_RETURNCMD | TPM_NONOTIFY, point.x, point.y, 0, self._hwnd, None)
        self.user32.DestroyMenu(menu)
        action = command_map.get(int(chosen))
        if action:
            action()

    def _dispatch_notification(self, notification: int) -> bool:
        if notification == WM_LBUTTONUP:
            if self._default_action is not None:
                self._default_action()
            return True
        if notification in (WM_RBUTTONUP, WM_CONTEXTMENU):
            self._show_menu()
            return True
        return False

    def _message_loop(self):
        class_name = f"RatVisionTrayWindow_{id(self)}"
        hinstance = self.kernel32.GetModuleHandleW(None)

        def wndproc(hwnd, message, wparam, lparam):
            if message == TRAY_MESSAGE and self._dispatch_notification(int(lparam)):
                return 0
            if message == WM_DESTROY:
                self.user32.PostQuitMessage(0)
                return 0
            return self.user32.DefWindowProcW(hwnd, message, wparam, lparam)

        self._wndproc = _WNDPROC(wndproc)
        wc = WNDCLASSW()
        wc.lpfnWndProc = self._wndproc
        wc.hInstance = hinstance
        wc.lpszClassName = class_name
        self.user32.RegisterClassW(ctypes.byref(wc))
        self._hwnd = self.user32.CreateWindowExW(0, class_name, "RAT VISION Tray", 0, 0, 0, 0, 0, None, None, hinstance, None)
        if not self._hwnd:
            self._ready.set()
            return
        self._ready.set()
        msg = wintypes.MSG()
        while self.user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
            self.user32.TranslateMessage(ctypes.byref(msg))
            self.user32.DispatchMessageW(ctypes.byref(msg))
        self._hwnd = None
