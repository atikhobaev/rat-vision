import ctypes
from ctypes import wintypes

from ratvision.platform.windows.gamma import GammaNativeApi
from ratvision.platform.windows.foreground import _WINEVENTPROC, configure_user32_signatures
from ratvision.platform.windows.tray import configure_tray_signatures


class FakeFunction:
    def __init__(self, result=1):
        self.result = result
        self.argtypes = None
        self.restype = ctypes.c_int

    def __call__(self, *_args):
        return self.result


class FakeGdi32:
    def __init__(self):
        self.CreateDCW = FakeFunction(0x1234567887654321)
        self.DeleteDC = FakeFunction(1)
        self.GetDeviceGammaRamp = FakeFunction(1)
        self.SetDeviceGammaRamp = FakeFunction(1)


class FakeUser32:
    def __init__(self):
        self.SetWinEventHook = FakeFunction(0x1234567887654321)
        self.UnhookWinEvent = FakeFunction(1)
        self.GetWindowThreadProcessId = FakeFunction(1)
        self.GetWindowTextLengthW = FakeFunction(0)
        self.GetWindowTextW = FakeFunction(0)


class FakeTrayUser32:
    def __init__(self):
        for name in (
            "PostMessageW", "DestroyIcon", "LoadImageW", "CreatePopupMenu",
            "AppendMenuW", "GetCursorPos", "SetForegroundWindow", "TrackPopupMenu",
            "DestroyMenu", "RegisterClassW", "CreateWindowExW", "GetMessageW",
            "TranslateMessage", "DispatchMessageW", "DefWindowProcW",
        ):
            setattr(self, name, FakeFunction())


class FakeShell32:
    def __init__(self):
        self.Shell_NotifyIconW = FakeFunction(1)


class FakeKernel32:
    def __init__(self):
        self.GetModuleHandleW = FakeFunction(0x1234567887654321)


def test_gamma_native_api_configures_pointer_sized_hdc_signature():
    gdi32 = FakeGdi32()
    GammaNativeApi(gdi32=gdi32)
    assert gdi32.CreateDCW.restype is wintypes.HDC
    assert gdi32.CreateDCW.argtypes[1] is wintypes.LPCWSTR
    assert gdi32.DeleteDC.argtypes == [wintypes.HDC]


def test_foreground_hook_configures_pointer_sized_hook_signature():
    user32 = FakeUser32()
    configure_user32_signatures(user32)
    assert user32.SetWinEventHook.restype is wintypes.HANDLE
    assert len(user32.SetWinEventHook.argtypes) == 7
    assert user32.SetWinEventHook.argtypes[0] is wintypes.DWORD
    assert user32.SetWinEventHook.argtypes[3] is _WINEVENTPROC
    assert user32.UnhookWinEvent.argtypes == [wintypes.HANDLE]
    assert user32.GetWindowThreadProcessId.argtypes[0] is wintypes.HWND


def test_tray_configures_pointer_sized_window_and_icon_handles():
    user32 = FakeTrayUser32()
    shell32 = FakeShell32()
    kernel32 = FakeKernel32()
    configure_tray_signatures(user32, shell32, kernel32)
    assert kernel32.GetModuleHandleW.restype is wintypes.HMODULE
    assert user32.CreateWindowExW.restype is wintypes.HWND
    assert user32.LoadImageW.restype is wintypes.HANDLE
    assert user32.CreatePopupMenu.restype is wintypes.HMENU
    assert user32.DefWindowProcW.restype is wintypes.LPARAM
    assert shell32.Shell_NotifyIconW.restype is wintypes.BOOL
