from ratvision.domain.models import DisplayInfo, VisualParameters
from ratvision.platform.simulation import (
    SimulationColorBackend,
    SimulationDisplayProvider,
    SimulationForegroundProvider,
    SimulationStartupBackend,
    SimulationTrayBackend,
)


def test_simulated_foreground_emits_normalized_executable():
    provider = SimulationForegroundProvider()
    seen = []
    provider.start(seen.append)
    provider.focus("HuntGame.EXE")
    assert seen[-1].executable == "huntgame.exe"
    assert provider.current().executable == "huntgame.exe"


def test_simulated_color_backend_records_capture_apply_restore():
    backend = SimulationColorBackend()
    params = VisualParameters(0.6, 0.7, 1.2, 55)
    backend.capture("DISPLAY1")
    backend.apply("DISPLAY1", params)
    backend.restore("DISPLAY1")
    assert backend.captured == {"DISPLAY1"}
    assert backend.applied == [("DISPLAY1", params)]
    assert backend.restored == ["DISPLAY1"]


def test_simulated_display_provider_can_change_displays():
    provider = SimulationDisplayProvider([])
    displays = [DisplayInfo("D1", "Main", 1920, 1080, 60.0, True, True)]
    provider.set_displays(displays)
    assert provider.list_displays() == displays


def test_simulated_tray_and_startup_keep_state():
    tray = SimulationTrayBackend()
    tray.start(None)
    tray.set_enabled(True)
    startup = SimulationStartupBackend()
    startup.set_enabled(True)
    assert tray.enabled is True
    assert startup.is_enabled() is True
    tray.stop()
    assert tray.running is False
