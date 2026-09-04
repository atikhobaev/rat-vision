from __future__ import annotations

# RAT VISION modification/reimplementation, 2026-09-03.
# The gamma-ramp behavior was derived from incheon-kim/tarkov-settings;
# see LICENSE and LICENSES.md (LGPL-2.1 and attribution details).

import ctypes
from ctypes import wintypes
import math
import sys
import threading

from ratvision.domain.models import VisualParameters
from ratvision.platform.base import PlatformUnavailableError


RampTuple = tuple[tuple[int, ...], tuple[int, ...], tuple[int, ...]]


def calculate_lut(params: VisualParameters) -> tuple[int, ...]:
    params = params.normalized()
    data_points = 256
    gamma = min(max(params.gamma, 0.4), 2.8)
    contrast = (min(max(params.contrast, 0.0), 1.0) - 0.5) * 2.0
    brightness = (min(max(params.brightness, 0.0), 1.0) - 0.5) * 2.0
    offset = contrast * (-25.4 if contrast > 0 else -32.0)
    value_range = (data_points - 1) + offset * 2.0
    offset += brightness * (value_range / 5.0)
    result: list[int] = []
    for index in range(data_points):
        factor = (index + offset) / value_range
        if factor <= 0.0:
            powered = 0.0
        else:
            powered = math.pow(factor, 1.0 / gamma)
        powered = min(max(powered, 0.0), 1.0)
        result.append(int(round(powered * 65535.0)))
    return tuple(result)


class _GammaRamp(ctypes.Structure):
    _fields_ = [
        ("red", ctypes.c_ushort * 256),
        ("green", ctypes.c_ushort * 256),
        ("blue", ctypes.c_ushort * 256),
    ]


class GammaNativeApi:
    def __init__(self, *, gdi32=None):
        if gdi32 is None:
            if sys.platform != "win32":
                raise PlatformUnavailableError("Gamma control requires Windows")
            gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)
        self.gdi32 = gdi32
        self.gdi32.CreateDCW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.LPVOID]
        self.gdi32.CreateDCW.restype = wintypes.HDC
        self.gdi32.DeleteDC.argtypes = [wintypes.HDC]
        self.gdi32.DeleteDC.restype = wintypes.BOOL
        self.gdi32.GetDeviceGammaRamp.argtypes = [wintypes.HDC, wintypes.LPVOID]
        self.gdi32.GetDeviceGammaRamp.restype = wintypes.BOOL
        self.gdi32.SetDeviceGammaRamp.argtypes = [wintypes.HDC, wintypes.LPVOID]
        self.gdi32.SetDeviceGammaRamp.restype = wintypes.BOOL

    def _with_dc(self, display_id: str, action):
        hdc = self.gdi32.CreateDCW(None, display_id, None, None)
        if not hdc:
            raise OSError(ctypes.get_last_error(), f"CreateDCW failed for {display_id}")
        try:
            return action(hdc)
        finally:
            self.gdi32.DeleteDC(hdc)

    def get_ramp(self, display_id: str) -> RampTuple:
        def read(hdc):
            ramp = _GammaRamp()
            if not self.gdi32.GetDeviceGammaRamp(hdc, ctypes.byref(ramp)):
                raise OSError(ctypes.get_last_error(), f"GetDeviceGammaRamp failed for {display_id}")
            return (
                tuple(int(v) for v in ramp.red),
                tuple(int(v) for v in ramp.green),
                tuple(int(v) for v in ramp.blue),
            )
        return self._with_dc(display_id, read)

    def set_ramp(self, display_id: str, values: RampTuple) -> bool:
        def write(hdc):
            ramp = _GammaRamp()
            for index in range(256):
                ramp.red[index] = values[0][index]
                ramp.green[index] = values[1][index]
                ramp.blue[index] = values[2][index]
            return bool(self.gdi32.SetDeviceGammaRamp(hdc, ctypes.byref(ramp)))
        return bool(self._with_dc(display_id, write))


class GammaController:
    def __init__(self, *, api=None, reapply_interval: float = 0.25):
        self.api = api or GammaNativeApi()
        self.baselines: dict[str, RampTuple] = {}
        self.reapply_interval = float(reapply_interval)
        self._desired: dict[str, RampTuple] = {}
        self._stop_events: dict[str, threading.Event] = {}
        self._threads: dict[str, threading.Thread] = {}
        self._lock = threading.RLock()

    def capture(self, display_id: str) -> None:
        if display_id not in self.baselines:
            self.baselines[display_id] = self.api.get_ramp(display_id)

    def _worker(self, display_id: str, stop_event: threading.Event) -> None:
        while not stop_event.wait(self.reapply_interval):
            with self._lock:
                ramp = self._desired.get(display_id)
            if ramp is None:
                return
            try:
                self.api.set_ramp(display_id, ramp)
            except Exception:
                return

    def apply(self, display_id: str, params: VisualParameters) -> None:
        self.capture(display_id)
        lut = calculate_lut(params)
        ramp: RampTuple = (lut, lut, lut)
        if not self.api.set_ramp(display_id, ramp):
            raise OSError(f"SetDeviceGammaRamp failed for {display_id}")
        with self._lock:
            self._desired[display_id] = ramp
            thread = self._threads.get(display_id)
            if thread is None or not thread.is_alive():
                stop_event = threading.Event()
                self._stop_events[display_id] = stop_event
                thread = threading.Thread(
                    target=self._worker,
                    args=(display_id, stop_event),
                    name=f"RatVisionGamma-{display_id}",
                    daemon=True,
                )
                self._threads[display_id] = thread
                thread.start()

    def _stop_worker(self, display_id: str) -> None:
        with self._lock:
            stop_event = self._stop_events.pop(display_id, None)
            thread = self._threads.pop(display_id, None)
            self._desired.pop(display_id, None)
        if stop_event is not None:
            stop_event.set()
        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=max(0.05, self.reapply_interval * 2.0))

    def restore(self, display_id: str) -> None:
        self._stop_worker(display_id)
        baseline = self.baselines.get(display_id)
        if baseline is not None:
            self.api.set_ramp(display_id, baseline)

    def restore_all(self) -> None:
        for display_id in list(self.baselines):
            self.restore(display_id)
