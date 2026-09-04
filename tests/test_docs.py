from pathlib import Path

from ratvision import __version__


def test_readme_mentions_current_version_and_python_simulation_workflow():
    readme = Path("README.md").read_text(encoding="utf-8")
    assert f"RAT VISION v{__version__}" in readme
    assert "python -m ratvision --simulate" in readme
    assert "Escape from Tarkov: Arena" in readme
    assert "Hunt: Showdown" in readme


def test_windows_scripts_use_python_runtime_and_pytest_not_wpf_commands():
    start = Path("scripts/start-rat-vision.bat").read_text(encoding="utf-8")
    build = Path("scripts/build-windows.bat").read_text(encoding="utf-8")
    build_ps1 = Path("scripts/build-windows.ps1").read_text(encoding="utf-8")
    verify = Path("scripts/verify.bat").read_text(encoding="utf-8")
    combined = "\n".join((start, build, build_ps1, verify)).lower()
    assert "python -m ratvision" in start.lower()
    assert "pytest" in verify.lower()
    assert "pyinstaller" in combined
    assert "dotnet" not in combined
    assert "msbuild" not in combined


def test_readme_contains_windows_hardware_verification_checklist():
    readme = Path("README.md").read_text(encoding="utf-8").lower()
    for phrase in (
        "global off restore",
        "alt-tab restore/reapply",
        "two-monitor independent restore",
        "nvidia saturation",
        "tray off/on lamp",
        "exit restore",
    ):
        assert phrase in readme


def test_windows_build_bootstraps_private_python_and_pauses_on_failure():
    bat = Path("scripts/build-windows.bat").read_text(encoding="utf-8").lower()
    ps1_path = Path("scripts/build-windows.ps1")
    assert ps1_path.exists()
    ps1 = ps1_path.read_text(encoding="utf-8").lower()
    combined = bat + "\n" + ps1
    assert "-m pip install" in combined
    assert "invoke-expression" not in combined
    assert "3.13" in combined
    assert ".runtime" in combined
    assert "pause" in bat
    assert "build.log" in combined
    assert "python 3.13 x64 is required" not in combined


def test_readme_says_system_python_is_not_required_for_one_click_build():
    readme = Path("README.md").read_text(encoding="utf-8").lower()
    assert "system python is not required" in readme
    assert "downloads the official cpython 3.13.15 x64 installer" in readme
    assert "tcl/tk enabled" in readme


def test_windows_build_uses_official_cpython_with_tcl_tk_and_verifies_hash():
    ps1 = Path("scripts/build-windows.ps1").read_text(encoding="utf-8").lower()
    assert "$pythonversion = '3.13.15'" in ps1
    assert "python-$pythonversion-amd64.exe" in ps1
    assert "include_tcltk=1" in ps1
    assert "get-filehash" in ps1 and "sha256" in ps1
    assert "edec09c4853aeae9ac36efb8c9f95b6b8e2fee65eee56d9767a8b7c69c574403" in ps1
    assert "uv python install" not in ps1
    assert "tkinter as tk" in ps1
    assert "tkversion" in ps1


def test_windows_build_pins_tcl_tk_library_paths_and_isolates_gui_tests():
    ps1 = Path("scripts/build-windows.ps1").read_text(encoding="utf-8").lower()
    assert "$env:tcl_library" in ps1
    assert "$env:tk_library" in ps1
    assert "init.tcl" in ps1
    assert "tk.tcl" in ps1
    assert "--ignore=tests/ui" in ps1
    assert "--ignore=tests/test_app_smoke.py" in ps1
    assert "--collect-only" in ps1
    assert "foreach ($nodeid" in ps1


def test_windows_runtime_isolates_private_nvapi_and_tk_cross_thread_callbacks():
    color = Path("ratvision/platform/windows/color_backend.py").read_text(encoding="utf-8")
    dvc = Path("ratvision/platform/windows/dvc_subprocess.py").read_text(encoding="utf-8")
    controller = Path("ratvision/controller.py").read_text(encoding="utf-8")
    app = Path("ratvision/app.py").read_text(encoding="utf-8")
    assert "DvcSubprocessController" in color
    assert "--dvc-helper" in dvc
    assert "_ui_queue" in controller and "_drain_ui_queue" in controller
    assert 'argv[0] == "--dvc-helper"' in app


def test_public_readme_does_not_name_upstream_repository():
    readme = Path("README.md").read_text(encoding="utf-8").lower()
    assert "incheon-kim/tarkov-settings" not in readme
    assert "github.com/incheon-kim" not in readme


def test_readme_documents_global_profile_quick_toggles_tooltips_and_tour():
    readme = Path("README.md").read_text(encoding="utf-8").lower()
    for phrase in ("global profile", "quick on/off", "tooltips", "tutorial tour"):
        assert phrase in readme


def test_readme_documents_v111_window_tour_display_and_settings_behavior():
    readme = Path("README.md").read_text(encoding="utf-8").lower()
    for phrase in (
        "always on top",
        "draggable help cards",
        "system-reported monitor name",
        "working settings toggles",
        "start minimized to tray",
        "closing the window minimizes to tray",
    ):
        assert phrase in readme


def test_windows_build_embeds_multisize_rat_vision_exe_icon():
    from PIL import Image

    icon_path = Path("ratvision/resources/brand/ratvision.ico")
    assert icon_path.exists()

    with Image.open(icon_path) as icon:
        sizes = set(icon.info.get("sizes", ()))
    for size in ((16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)):
        assert size in sizes

    ps1 = Path("scripts/build-windows.ps1").read_text(encoding="utf-8")
    assert "--icon" in ps1
    assert "ratvision\\resources\\brand\\ratvision.ico" in ps1
