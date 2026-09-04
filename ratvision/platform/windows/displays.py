from __future__ import annotations

import ctypes
from ctypes import wintypes
import sys
from collections.abc import Callable

from ratvision.domain.models import DisplayInfo
from ratvision.platform.base import PlatformUnavailableError

MONITORINFOF_PRIMARY = 0x00000001
DISPLAY_DEVICE_ACTIVE = 0x00000001
QDC_ONLY_ACTIVE_PATHS = 0x00000002
DISPLAYCONFIG_DEVICE_INFO_GET_SOURCE_NAME = 1
DISPLAYCONFIG_DEVICE_INFO_GET_TARGET_NAME = 2
ERROR_SUCCESS = 0
ERROR_INSUFFICIENT_BUFFER = 122

UINT32 = ctypes.c_uint32
UINT16 = ctypes.c_uint16


class RECT(ctypes.Structure):
    _fields_ = [("left", wintypes.LONG), ("top", wintypes.LONG), ("right", wintypes.LONG), ("bottom", wintypes.LONG)]


class MONITORINFOEXW(ctypes.Structure):
    _fields_ = [
        ("cbSize", wintypes.DWORD),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", wintypes.DWORD),
        ("szDevice", wintypes.WCHAR * 32),
    ]


class DISPLAY_DEVICEW(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("DeviceName", wintypes.WCHAR * 32),
        ("DeviceString", wintypes.WCHAR * 128),
        ("StateFlags", wintypes.DWORD),
        ("DeviceID", wintypes.WCHAR * 128),
        ("DeviceKey", wintypes.WCHAR * 128),
    ]


class LUID(ctypes.Structure):
    _fields_ = [("LowPart", wintypes.DWORD), ("HighPart", wintypes.LONG)]


class DISPLAYCONFIG_RATIONAL(ctypes.Structure):
    _fields_ = [("Numerator", UINT32), ("Denominator", UINT32)]


class DISPLAYCONFIG_PATH_SOURCE_INFO(ctypes.Structure):
    _fields_ = [
        ("adapterId", LUID),
        ("id", UINT32),
        ("modeInfoIdx", UINT32),
        ("statusFlags", UINT32),
    ]


class DISPLAYCONFIG_PATH_TARGET_INFO(ctypes.Structure):
    _fields_ = [
        ("adapterId", LUID),
        ("id", UINT32),
        ("modeInfoIdx", UINT32),
        ("outputTechnology", UINT32),
        ("rotation", UINT32),
        ("scaling", UINT32),
        ("refreshRate", DISPLAYCONFIG_RATIONAL),
        ("scanLineOrdering", UINT32),
        ("targetAvailable", wintypes.BOOL),
        ("statusFlags", UINT32),
    ]


class DISPLAYCONFIG_PATH_INFO(ctypes.Structure):
    _fields_ = [
        ("sourceInfo", DISPLAYCONFIG_PATH_SOURCE_INFO),
        ("targetInfo", DISPLAYCONFIG_PATH_TARGET_INFO),
        ("flags", UINT32),
    ]


class DISPLAYCONFIG_DEVICE_INFO_HEADER(ctypes.Structure):
    _fields_ = [
        ("type", UINT32),
        ("size", UINT32),
        ("adapterId", LUID),
        ("id", UINT32),
    ]


class DISPLAYCONFIG_SOURCE_DEVICE_NAME(ctypes.Structure):
    _fields_ = [
        ("header", DISPLAYCONFIG_DEVICE_INFO_HEADER),
        ("viewGdiDeviceName", wintypes.WCHAR * 32),
    ]


class DISPLAYCONFIG_TARGET_DEVICE_NAME(ctypes.Structure):
    _fields_ = [
        ("header", DISPLAYCONFIG_DEVICE_INFO_HEADER),
        ("flags", UINT32),
        ("outputTechnology", UINT32),
        ("edidManufactureId", UINT16),
        ("edidProductCodeId", UINT16),
        ("connectorInstance", UINT32),
        ("monitorFriendlyDeviceName", wintypes.WCHAR * 64),
        ("monitorDevicePath", wintypes.WCHAR * 128),
    ]


def configure_display_signatures(user32, monitor_callback_type) -> None:
    user32.GetMonitorInfoW.argtypes = [wintypes.HMONITOR, ctypes.POINTER(MONITORINFOEXW)]
    user32.GetMonitorInfoW.restype = wintypes.BOOL
    user32.EnumDisplayMonitors.argtypes = [wintypes.HDC, ctypes.POINTER(RECT), monitor_callback_type, wintypes.LPARAM]
    user32.EnumDisplayMonitors.restype = wintypes.BOOL
    user32.EnumDisplayDevicesW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, ctypes.POINTER(DISPLAY_DEVICEW), wintypes.DWORD]
    user32.EnumDisplayDevicesW.restype = wintypes.BOOL


def _configure_displayconfig_signatures(user32) -> None:
    user32.GetDisplayConfigBufferSizes.argtypes = [UINT32, ctypes.POINTER(UINT32), ctypes.POINTER(UINT32)]
    user32.GetDisplayConfigBufferSizes.restype = wintypes.LONG
    user32.QueryDisplayConfig.argtypes = [
        UINT32,
        ctypes.POINTER(UINT32),
        ctypes.POINTER(DISPLAYCONFIG_PATH_INFO),
        ctypes.POINTER(UINT32),
        ctypes.c_void_p,
        ctypes.c_void_p,
    ]
    user32.QueryDisplayConfig.restype = wintypes.LONG
    user32.DisplayConfigGetDeviceInfo.argtypes = [ctypes.c_void_p]
    user32.DisplayConfigGetDeviceInfo.restype = wintypes.LONG


def _device_info_header(kind: int, struct_type, adapter: LUID, device_id: int) -> DISPLAYCONFIG_DEVICE_INFO_HEADER:
    return DISPLAYCONFIG_DEVICE_INFO_HEADER(
        type=kind,
        size=ctypes.sizeof(struct_type),
        adapterId=adapter,
        id=device_id,
    )


def displayconfig_friendly_names(user32) -> dict[str, str]:
    """Map active GDI display ids such as DISPLAY1 to EDID-friendly names.

    Windows' older ``EnumDisplayDevicesW`` API often reports only
    ``Generic PnP Monitor``.  The CCD/DisplayConfig API exposes the monitor
    friendly name Windows builds from EDID, so use that as the primary UI name.
    """
    required = ("GetDisplayConfigBufferSizes", "QueryDisplayConfig", "DisplayConfigGetDeviceInfo")
    if not all(hasattr(user32, name) for name in required):
        return {}
    try:
        # Real ctypes functions need explicit signatures; Python fake functions in
        # tests intentionally do not expose argtypes/restype and can be called as-is.
        if hasattr(user32.GetDisplayConfigBufferSizes, "argtypes"):
            _configure_displayconfig_signatures(user32)
    except (AttributeError, TypeError):
        pass

    for _attempt in range(3):
        path_count = UINT32(0)
        mode_count = UINT32(0)
        status = int(user32.GetDisplayConfigBufferSizes(QDC_ONLY_ACTIVE_PATHS, ctypes.byref(path_count), ctypes.byref(mode_count)))
        if status != ERROR_SUCCESS or path_count.value == 0:
            return {}

        paths = (DISPLAYCONFIG_PATH_INFO * path_count.value)()
        # We never inspect mode data; over-allocate a suitably aligned raw buffer.
        # QueryDisplayConfig uses its native DISPLAYCONFIG_MODE_INFO stride.
        mode_bytes = max(1, mode_count.value) * 128
        modes = (ctypes.c_ubyte * mode_bytes)()
        topology = None
        status = int(
            user32.QueryDisplayConfig(
                QDC_ONLY_ACTIVE_PATHS,
                ctypes.byref(path_count),
                paths,
                ctypes.byref(mode_count),
                modes,
                topology,
            )
        )
        if status == ERROR_INSUFFICIENT_BUFFER:
            continue
        if status != ERROR_SUCCESS:
            return {}

        result: dict[str, str] = {}
        for path in paths[: path_count.value]:
            source = DISPLAYCONFIG_SOURCE_DEVICE_NAME()
            source.header = _device_info_header(
                DISPLAYCONFIG_DEVICE_INFO_GET_SOURCE_NAME,
                DISPLAYCONFIG_SOURCE_DEVICE_NAME,
                path.sourceInfo.adapterId,
                int(path.sourceInfo.id),
            )
            if int(user32.DisplayConfigGetDeviceInfo(ctypes.byref(source))) != ERROR_SUCCESS:
                continue
            gdi_name = str(source.viewGdiDeviceName).strip()
            if not gdi_name:
                continue

            target = DISPLAYCONFIG_TARGET_DEVICE_NAME()
            target.header = _device_info_header(
                DISPLAYCONFIG_DEVICE_INFO_GET_TARGET_NAME,
                DISPLAYCONFIG_TARGET_DEVICE_NAME,
                path.targetInfo.adapterId,
                int(path.targetInfo.id),
            )
            if int(user32.DisplayConfigGetDeviceInfo(ctypes.byref(target))) != ERROR_SUCCESS:
                continue
            friendly = str(target.monitorFriendlyDeviceName).strip()
            if friendly:
                result[gdi_name] = friendly
        return result
    return {}


def friendly_monitor_name(user32, display_id: str, *, displayconfig_names: dict[str, str] | None = None) -> str | None:
    """Return the best monitor name Windows exposes for a GDI display device."""
    if displayconfig_names:
        direct = displayconfig_names.get(display_id)
        if direct:
            return direct
        folded = display_id.casefold()
        for key, value in displayconfig_names.items():
            if key.casefold() == folded and value:
                return value

    first_name: str | None = None
    for index in range(16):
        device = DISPLAY_DEVICEW()
        device.cb = ctypes.sizeof(device)
        if not user32.EnumDisplayDevicesW(display_id, index, ctypes.byref(device), 0):
            break
        name = str(device.DeviceString).strip()
        if not name:
            continue
        if first_name is None:
            first_name = name
        if device.StateFlags & DISPLAY_DEVICE_ACTIVE:
            return name
    return first_name


class WindowsDisplayProvider:
    def __init__(self, *, enumerator: Callable[[], list[dict]] | None = None, user32=None):
        if enumerator is None and user32 is None and sys.platform != "win32":
            raise PlatformUnavailableError("Windows display enumeration requires Windows")
        self._enumerator = enumerator
        self._user32 = user32

    def list_displays(self) -> list[DisplayInfo]:
        rows = self._enumerator() if self._enumerator else self._enumerate_win32()
        return [
            DisplayInfo(
                str(row["id"]),
                str(row.get("name") or row["id"]),
                int(row.get("width") or 0),
                int(row.get("height") or 0),
                float(row["refresh_hz"]) if row.get("refresh_hz") is not None else None,
                bool(row.get("primary", False)),
                bool(row.get("online", True)),
            )
            for row in rows
        ]

    def _enumerate_win32(self) -> list[dict]:
        user32 = self._user32 or ctypes.WinDLL("user32", use_last_error=True)
        rows: list[dict] = []
        factory = getattr(ctypes, "WINFUNCTYPE", ctypes.CFUNCTYPE)
        callback_type = factory(wintypes.BOOL, wintypes.HMONITOR, wintypes.HDC, ctypes.POINTER(RECT), wintypes.LPARAM)
        configure_display_signatures(user32, callback_type)
        displayconfig_names = displayconfig_friendly_names(user32)

        def callback(hmonitor, _hdc, _rect, _data):
            info = MONITORINFOEXW()
            info.cbSize = ctypes.sizeof(info)
            if not user32.GetMonitorInfoW(hmonitor, ctypes.byref(info)):
                return True
            rect = info.rcMonitor
            device = str(info.szDevice)
            name = friendly_monitor_name(user32, device, displayconfig_names=displayconfig_names) or device
            rows.append(
                {
                    "id": device,
                    "name": name,
                    "width": rect.right - rect.left,
                    "height": rect.bottom - rect.top,
                    "refresh_hz": None,
                    "primary": bool(info.dwFlags & MONITORINFOF_PRIMARY),
                    "online": True,
                }
            )
            return True

        native_callback = callback_type(callback)
        if not user32.EnumDisplayMonitors(None, None, native_callback, 0):
            raise OSError(ctypes.get_last_error(), "EnumDisplayMonitors failed")
        return rows
