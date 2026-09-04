from __future__ import annotations

# RAT VISION NVAPI reimplementation, 2026-09-03.
# Behavior was researched from the LGPL upstream references identified in
# LICENSES.md; this Python ctypes implementation is modified/new RAT VISION code.

import ctypes
from dataclasses import dataclass
import sys

from ratvision.platform.base import PlatformUnavailableError

NVAPI_OK = 0
FN_INITIALIZE = 0x0150E828
FN_UNLOAD = 0xD22BDD7E
FN_GET_ASSOCIATED_DISPLAY_HANDLE = 0x35C29134
FN_GET_DVC_INFO = 0x4085DE45
FN_SET_DVC_LEVEL = 0x172409B4


class NvApiError(RuntimeError):
    def __init__(self, operation: str, status: int):
        super().__init__(f"{operation} failed with NVAPI status {status}")
        self.operation = operation
        self.status = int(status)


class _DvcInfoNative(ctypes.Structure):
    _pack_ = 8
    _fields_ = [
        ("version", ctypes.c_uint32),
        ("current_level", ctypes.c_int32),
        ("minimum_level", ctypes.c_int32),
        ("maximum_level", ctypes.c_int32),
    ]

    @classmethod
    def initialized(cls):
        value = cls()
        value.version = ctypes.sizeof(cls) | (1 << 16)
        return value


@dataclass(frozen=True, slots=True)
class DvcInfo:
    current: int
    minimum: int
    maximum: int


class NvApiNative:
    def __init__(self, *, resolver=None, library=None):
        self._injected_resolver = resolver
        self._library = library
        self._query = None
        if resolver is None:
            if library is None:
                if sys.platform != "win32":
                    raise PlatformUnavailableError("NVIDIA NVAPI requires Windows")
                library = ctypes.WinDLL("nvapi64.dll")
                self._library = library
            self._query = library.nvapi_QueryInterface
            self._query.argtypes = [ctypes.c_uint32]
            self._query.restype = ctypes.c_void_p

    @staticmethod
    def _factory():
        return getattr(ctypes, "WINFUNCTYPE", ctypes.CFUNCTYPE)

    def _function(self, function_id: int, restype, *argtypes):
        if self._injected_resolver is not None:
            return self._injected_resolver(function_id)
        address = self._query(ctypes.c_uint32(function_id))
        if not address:
            raise NvApiError(f"resolve 0x{function_id:08X}", -1)
        return self._factory()(restype, *argtypes)(address)

    @staticmethod
    def _check(operation: str, status: int) -> None:
        if int(status) != NVAPI_OK:
            raise NvApiError(operation, int(status))

    def initialize(self) -> None:
        fn = self._function(FN_INITIALIZE, ctypes.c_int)
        self._check("NvAPI_Initialize", fn())

    def unload(self) -> None:
        fn = self._function(FN_UNLOAD, ctypes.c_int)
        self._check("NvAPI_Unload", fn())

    def get_display_handle(self, display_name: str):
        fn = self._function(
            FN_GET_ASSOCIATED_DISPLAY_HANDLE,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.POINTER(ctypes.c_void_p),
        )
        handle = ctypes.c_void_p()
        status = fn(display_name.encode("ascii", errors="strict"), ctypes.byref(handle))
        self._check("NvAPI_GetAssociatedNvidiaDisplayHandle", status)
        return handle.value

    def get_dvc_info(self, handle) -> DvcInfo:
        fn = self._function(
            FN_GET_DVC_INFO,
            ctypes.c_int,
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.POINTER(_DvcInfoNative),
        )
        info = _DvcInfoNative.initialized()
        status = fn(ctypes.c_void_p(handle) if isinstance(handle, int) else handle, ctypes.c_uint32(0), ctypes.byref(info))
        self._check("NvAPI_GetDVCInfo", status)
        return DvcInfo(int(info.current_level), int(info.minimum_level), int(info.maximum_level))

    def set_dvc_level(self, handle, level: int) -> None:
        fn = self._function(
            FN_SET_DVC_LEVEL,
            ctypes.c_int,
            ctypes.c_void_p,
            ctypes.c_uint32,
            ctypes.c_int32,
        )
        status = fn(ctypes.c_void_p(handle) if isinstance(handle, int) else handle, ctypes.c_uint32(0), ctypes.c_int32(int(level)))
        self._check("NvAPI_SetDVCLevel", status)


class NvApiDvcController:
    def __init__(self, *, native=None):
        self.native = native or NvApiNative()
        self.native.initialize()
        self.handles: dict[str, object] = {}
        self.originals: dict[str, int] = {}
        self.ranges: dict[str, tuple[int, int]] = {}

    def _handle(self, display_id: str):
        if display_id not in self.handles:
            self.handles[display_id] = self.native.get_display_handle(display_id)
        return self.handles[display_id]

    def capture(self, display_id: str) -> None:
        if display_id in self.originals:
            return
        handle = self._handle(display_id)
        info = self.native.get_dvc_info(handle)
        self.originals[display_id] = info.current
        self.ranges[display_id] = (info.minimum, info.maximum)

    def set_level(self, display_id: str, level: int) -> None:
        self.capture(display_id)
        minimum, maximum = self.ranges[display_id]
        clamped = min(max(int(level), minimum), maximum)
        self.native.set_dvc_level(self._handle(display_id), clamped)

    def restore(self, display_id: str) -> None:
        if display_id in self.originals:
            self.native.set_dvc_level(self._handle(display_id), self.originals[display_id])

    def restore_all(self) -> None:
        for display_id in list(self.originals):
            self.restore(display_id)

    def capabilities(self, display_id: str) -> dict[str, object]:
        try:
            self.capture(display_id)
        except Exception as exc:
            return {"supported": False, "reason": str(exc)}
        minimum, maximum = self.ranges[display_id]
        return {"supported": True, "minimum": minimum, "maximum": maximum}

    def close(self) -> None:
        self.restore_all()
        self.native.unload()
