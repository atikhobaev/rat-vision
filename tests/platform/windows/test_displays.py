from ratvision.platform.windows.displays import WindowsDisplayProvider


def test_display_provider_maps_enumerated_rows():
    provider = WindowsDisplayProvider(enumerator=lambda: [
        {"id": r"\\.\DISPLAY1", "name": "LG 27", "width": 2560, "height": 1440, "refresh_hz": 165.0, "primary": True, "online": True},
        {"id": r"\\.\DISPLAY2", "name": "Dell", "width": 1920, "height": 1080, "refresh_hz": 60.0, "primary": False, "online": False},
    ])
    displays = provider.list_displays()
    assert displays[0].primary is True
    assert displays[0].refresh_hz == 165.0
    assert displays[1].online is False


def test_system_monitor_friendly_name_is_read_from_enum_display_devices():
    from ratvision.platform.windows.displays import friendly_monitor_name

    class FakeUser32:
        def EnumDisplayDevicesW(self, device_name, index, out_device, flags):
            assert device_name == r"\\.\DISPLAY1"
            if index > 0:
                return 0
            row = out_device._obj
            row.DeviceString = "LG ULTRAGEAR 27GP850"
            row.DeviceName = r"\\.\DISPLAY1\Monitor0"
            row.StateFlags = 1
            return 1

    assert friendly_monitor_name(FakeUser32(), r"\\.\DISPLAY1") == "LG ULTRAGEAR 27GP850"


def test_display_provider_configures_pointer_safe_winapi_signatures():
    import ctypes
    from ctypes import wintypes
    from ratvision.platform.windows.displays import configure_display_signatures

    class FakeFunction:
        def __init__(self):
            self.argtypes = None
            self.restype = ctypes.c_int
        def __call__(self, *_args):
            return 1

    class FakeUser32:
        def __init__(self):
            self.GetMonitorInfoW = FakeFunction()
            self.EnumDisplayMonitors = FakeFunction()
            self.EnumDisplayDevicesW = FakeFunction()

    user32 = FakeUser32()
    configure_display_signatures(user32, ctypes.c_void_p)
    assert user32.GetMonitorInfoW.argtypes[0] is wintypes.HMONITOR
    assert user32.GetMonitorInfoW.restype is wintypes.BOOL
    assert user32.EnumDisplayDevicesW.argtypes[0] is wintypes.LPCWSTR
    assert user32.EnumDisplayDevicesW.restype is wintypes.BOOL


def test_displayconfig_maps_gdi_source_to_edid_friendly_target_name():
    from ratvision.platform.windows.displays import displayconfig_friendly_names

    class FakeUser32:
        def GetDisplayConfigBufferSizes(self, flags, path_count, mode_count):
            assert flags == 0x00000002
            path_count._obj.value = 1
            mode_count._obj.value = 1
            return 0

        def QueryDisplayConfig(self, flags, path_count, paths, mode_count, modes, topology):
            assert flags == 0x00000002
            paths[0].sourceInfo.adapterId.LowPart = 7
            paths[0].sourceInfo.adapterId.HighPart = 0
            paths[0].sourceInfo.id = 11
            paths[0].targetInfo.adapterId.LowPart = 7
            paths[0].targetInfo.adapterId.HighPart = 0
            paths[0].targetInfo.id = 22
            path_count._obj.value = 1
            return 0

        def DisplayConfigGetDeviceInfo(self, packet):
            request = packet._obj
            if hasattr(request, "viewGdiDeviceName"):
                request.viewGdiDeviceName = r"\\.\DISPLAY1"
            else:
                request.monitorFriendlyDeviceName = "LG ULTRAGEAR 34GN850"
                request.flags = 1
            return 0

    names = displayconfig_friendly_names(FakeUser32())
    assert names[r"\\.\DISPLAY1"] == "LG ULTRAGEAR 34GN850"


def test_displayconfig_name_has_priority_over_generic_pnp_fallback():
    from ratvision.platform.windows.displays import friendly_monitor_name

    class FakeUser32:
        def EnumDisplayDevicesW(self, device_name, index, out_device, flags):
            if index > 0:
                return 0
            row = out_device._obj
            row.DeviceString = "Generic PnP Monitor"
            row.StateFlags = 1
            return 1

    assert friendly_monitor_name(
        FakeUser32(),
        r"\\.\DISPLAY1",
        displayconfig_names={r"\\.\DISPLAY1": "Dell U2723QE"},
    ) == "Dell U2723QE"
