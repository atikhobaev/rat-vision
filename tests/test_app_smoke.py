from ratvision import __version__
from ratvision.app import create_simulation_app
from ratvision.domain.models import ThemeMode


def test_simulation_app_builds_interactive_main_window(tmp_path):
    root, controller, window = create_simulation_app(settings_path=tmp_path / "settings.json")
    root.withdraw()
    root.update_idletasks()
    assert root.title() == f"RAT VISION v{__version__}"
    assert controller.platform_name == "simulation"
    assert len(controller.settings.profiles) == 4
    assert window.sidebar.donate_button.text == "☕ Buy me a coffee"
    controller.show_settings()
    root.update_idletasks()
    assert window.settings_view is not None
    controller.shutdown()


def test_simulation_app_accepts_theme_override(tmp_path):
    root, controller, _window = create_simulation_app(
        settings_path=tmp_path / "settings.json",
        theme_override=ThemeMode.DAY,
    )
    root.withdraw()
    root.update_idletasks()
    assert controller.settings.theme == ThemeMode.DAY
    assert controller.theme_manager.current.mode == ThemeMode.DAY
    controller.shutdown()


def test_frozen_dvc_helper_path_runs_without_creating_tk(monkeypatch):
    import ratvision.app as app

    called = {}

    def fake_helper(argv):
        called["argv"] = argv
        return 7

    monkeypatch.setattr(app, "run_dvc_helper_cli", fake_helper, raising=False)
    assert app.main(["--dvc-helper", "capture", "--display", "D1"]) == 7
    assert called["argv"] == ["capture", "--display", "D1"]
