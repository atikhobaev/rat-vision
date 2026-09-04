from ratvision.diagnostics.collector import DiagnosticsCollector
from ratvision.domain.models import DisplayInfo, ForegroundProcess


class Controller:
    version = "1.0.0"
    displays = [DisplayInfo("D1", "Main", 2560, 1440, 165.0, True, True)]
    current_foreground = ForegroundProcess(42, "huntgame.exe", "Hunt")

    class Settings:
        global_enabled = True

    settings = Settings()

    class Color:
        def capabilities(self, display_id):
            return {"gamma": True, "saturation": False}

    color_backend = Color()
    platform_name = "simulation"


def test_diagnostics_contains_version_xrat_foreground_and_displays():
    collector = DiagnosticsCollector(Controller())
    data = collector.collect()
    assert data["version"] == "1.0.0"
    assert data["xrat_enabled"] is True
    assert data["foreground_process"] == "huntgame.exe"
    assert data["display_count"] == 1
    assert data["displays"][0]["id"] == "D1"
    assert "RAT VISION v1.0.0" in collector.format_text()
