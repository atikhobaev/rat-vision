from ratvision.platform.windows.nvapi import (
    FN_GET_ASSOCIATED_DISPLAY_HANDLE,
    FN_GET_DVC_INFO,
    FN_INITIALIZE,
    FN_SET_DVC_LEVEL,
    FN_UNLOAD,
    NvApiNative,
    NvApiDvcController,
)


def test_nvapi_native_resolves_expected_ids_and_reads_dvc_info():
    called_ids = []

    def resolver(function_id):
        called_ids.append(function_id)
        if function_id in (FN_INITIALIZE, FN_UNLOAD):
            return lambda: 0
        if function_id == FN_GET_ASSOCIATED_DISPLAY_HANDLE:
            def get_handle(_name, out_handle):
                out_handle._obj.value = 0x1234
                return 0
            return get_handle
        if function_id == FN_GET_DVC_INFO:
            def get_info(_handle, _output_id, out_info):
                info = out_info._obj
                info.current_level = 42
                info.minimum_level = 0
                info.maximum_level = 100
                return 0
            return get_info
        if function_id == FN_SET_DVC_LEVEL:
            return lambda _handle, _output_id, _level: 0
        raise AssertionError(function_id)

    native = NvApiNative(resolver=resolver)
    native.initialize()
    handle = native.get_display_handle(r"\\.\DISPLAY1")
    info = native.get_dvc_info(handle)
    native.set_dvc_level(handle, 70)
    native.unload()
    assert handle == 0x1234
    assert (info.current, info.minimum, info.maximum) == (42, 0, 100)
    assert set(called_ids) == {
        FN_INITIALIZE,
        FN_UNLOAD,
        FN_GET_ASSOCIATED_DISPLAY_HANDLE,
        FN_GET_DVC_INFO,
        FN_SET_DVC_LEVEL,
    }


class FakeNative:
    def __init__(self):
        self.values = {"D1": 35}
        self.set_calls = []

    def initialize(self): pass
    def unload(self): pass
    def get_display_handle(self, display_id): return display_id
    def get_dvc_info(self, handle):
        from ratvision.platform.windows.nvapi import DvcInfo
        return DvcInfo(self.values[handle], 0, 100)
    def set_dvc_level(self, handle, level):
        self.values[handle] = level
        self.set_calls.append((handle, level))


def test_dvc_controller_captures_clamps_and_restores():
    native = FakeNative()
    dvc = NvApiDvcController(native=native)
    dvc.capture("D1")
    dvc.set_level("D1", 140)
    assert native.set_calls[-1] == ("D1", 100)
    dvc.restore("D1")
    assert native.set_calls[-1] == ("D1", 35)
