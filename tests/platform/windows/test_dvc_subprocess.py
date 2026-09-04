import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from ratvision.platform.windows.dvc_subprocess import (
    DvcHelperError,
    DvcSubprocessController,
    build_dvc_helper_command,
    execute_dvc_helper_operation,
)


class FakeNative:
    def __init__(self):
        self.calls = []

    def initialize(self): self.calls.append(("initialize",))
    def unload(self): self.calls.append(("unload",))
    def get_display_handle(self, display):
        self.calls.append(("handle", display)); return 1234
    def get_dvc_info(self, handle):
        from ratvision.platform.windows.nvapi import DvcInfo
        self.calls.append(("info", handle)); return DvcInfo(35, 0, 100)
    def set_dvc_level(self, handle, level):
        self.calls.append(("set", handle, level))


def test_execute_dvc_helper_capture_and_set_use_native_api():
    native = FakeNative()
    captured = execute_dvc_helper_operation("capture", r"\\.\DISPLAY1", None, native=native)
    assert captured == {"current": 35, "minimum": 0, "maximum": 100}
    assert native.calls[-1] == ("unload",)

    native.calls.clear()
    result = execute_dvc_helper_operation("set", r"\\.\DISPLAY1", 72, native=native)
    assert result == {"level": 72}
    assert ("set", 1234, 72) in native.calls
    assert native.calls[-1] == ("unload",)


def test_dvc_subprocess_controller_stores_baseline_and_restores_with_new_process_each_time(tmp_path):
    calls = []

    def runner(command, **kwargs):
        calls.append((command, kwargs))
        result_path = Path(command[command.index("--result-file") + 1])
        if "capture" in command:
            payload = {"ok": True, "result": {"current": 35, "minimum": 0, "maximum": 100}}
        else:
            level = int(command[command.index("--level") + 1])
            payload = {"ok": True, "result": {"level": level}}
        result_path.write_text(json.dumps(payload), encoding="utf-8")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    controller = DvcSubprocessController(runner=runner, executable="python", frozen=False, temp_dir=tmp_path)
    controller.capture("D1")
    controller.set_level("D1", 140)
    controller.restore("D1")

    assert controller.originals["D1"] == 35
    assert controller.ranges["D1"] == (0, 100)
    assert len(calls) == 3
    assert "100" in calls[1][0]
    assert "35" in calls[2][0]


def test_dvc_subprocess_native_crash_is_reported_as_python_exception(tmp_path):
    def runner(_command, **_kwargs):
        return SimpleNamespace(returncode=-1073741819, stdout="", stderr="")  # Windows access violation

    controller = DvcSubprocessController(runner=runner, executable="ratvision.exe", frozen=True, temp_dir=tmp_path)
    with pytest.raises(DvcHelperError) as exc:
        controller.capture("D1")
    assert "exited" in str(exc.value)
    assert "-1073741819" in str(exc.value)


def test_build_dvc_helper_command_supports_source_and_frozen_modes(tmp_path):
    result_file = tmp_path / "result.json"
    source = build_dvc_helper_command(
        "python.exe", frozen=False, operation="capture", display_id="D1", result_file=result_file
    )
    assert source[:3] == ["python.exe", "-m", "ratvision.platform.windows.dvc_helper"]
    assert source[-2:] == ["--result-file", str(result_file)]

    frozen = build_dvc_helper_command(
        "RAT VISION.exe", frozen=True, operation="set", display_id="D1", level=70, result_file=result_file
    )
    assert frozen[:2] == ["RAT VISION.exe", "--dvc-helper"]
    assert ["--level", "70"] == frozen[frozen.index("--level"):frozen.index("--level") + 2]
    assert frozen[-2:] == ["--result-file", str(result_file)]
