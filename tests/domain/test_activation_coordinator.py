from ratvision.domain.activation_coordinator import ActivationCoordinator
from ratvision.domain.models import AppSettings, DisplayInfo, ForegroundProcess, GameProfile, VisualParameters
from ratvision.domain.profile_service import ProfileService
from ratvision.platform.simulation import SimulationColorBackend


def build(enabled=True):
    settings = AppSettings(
        global_enabled=enabled,
        profiles=[
            GameProfile(
                id="eft",
                name="EFT",
                processes=["EscapeFromTarkov.exe"],
                display_ids=["D1", "D2"],
                visual=VisualParameters(0.6, 0.7, 1.2, 55),
            )
        ],
    )
    displays = {
        "D1": DisplayInfo("D1", "Main", 2560, 1440, 165.0, True, True),
        "D2": DisplayInfo("D2", "Second", 1920, 1080, 60.0, False, True),
    }
    backend = SimulationColorBackend()
    coordinator = ActivationCoordinator(settings, ProfileService(settings), backend, lambda: displays)
    return settings, backend, coordinator


def test_global_off_restores_all_and_blocks_matching():
    settings, backend, coordinator = build(True)
    coordinator.set_global_enabled(False)
    coordinator.on_foreground(ForegroundProcess(1, "escapefromtarkov.exe", ""))
    assert settings.global_enabled is False
    assert backend.applied == []
    assert backend.restore_all_count == 1


def test_matching_profile_applies_to_all_selected_online_displays():
    _, backend, coordinator = build(True)
    coordinator.on_foreground(ForegroundProcess(1, "EscapeFromTarkov.EXE", ""))
    assert [display for display, _ in backend.applied] == ["D1", "D2"]
    assert backend.captured == {"D1", "D2"}
    assert coordinator.active_profile_id == "eft"


def test_leaving_game_restores_active_profile_displays():
    _, backend, coordinator = build(True)
    coordinator.on_foreground(ForegroundProcess(1, "escapefromtarkov.exe", ""))
    coordinator.on_foreground(ForegroundProcess(2, "explorer.exe", "Desktop"))
    assert backend.restored[-2:] == ["D1", "D2"]
    assert coordinator.active_profile_id is None


def test_refresh_profile_reapplies_only_when_profile_is_live():
    _, backend, coordinator = build(True)
    coordinator.refresh_profile("eft")
    assert backend.applied == []
    coordinator.on_foreground(ForegroundProcess(1, "escapefromtarkov.exe", ""))
    first_count = len(backend.applied)
    coordinator.refresh_profile("eft")
    assert len(backend.applied) == first_count + 2


def test_global_profile_applies_when_no_specific_process_matches():
    settings = AppSettings(
        global_enabled=True,
        profiles=[
            GameProfile(id="global", name="Global", builtin_id="global", processes=[], display_ids=["D1"], visual=VisualParameters(0.55, 0.55, 1.1, 10)),
            GameProfile(id="eft", name="EFT", processes=["escapefromtarkov.exe"], display_ids=["D1"], visual=VisualParameters(0.7, 0.7, 1.3, 60)),
        ],
    )
    displays = {"D1": DisplayInfo("D1", "Main", 2560, 1440, 165.0, True, True)}
    backend = SimulationColorBackend()
    coordinator = ActivationCoordinator(settings, ProfileService(settings), backend, lambda: displays)

    coordinator.on_foreground(ForegroundProcess(2, "explorer.exe", "Desktop"))

    assert coordinator.active_profile_id == "global"
    assert backend.applied[-1] == ("D1", settings.profiles[0].visual)


def test_specific_profile_overrides_global_then_global_returns_after_alt_tab():
    settings = AppSettings(
        global_enabled=True,
        profiles=[
            GameProfile(id="global", name="Global", builtin_id="global", processes=[], display_ids=["D1"], visual=VisualParameters(0.55, 0.55, 1.1, 10)),
            GameProfile(id="eft", name="EFT", processes=["escapefromtarkov.exe"], display_ids=["D1"], visual=VisualParameters(0.7, 0.7, 1.3, 60)),
        ],
    )
    displays = {"D1": DisplayInfo("D1", "Main", 2560, 1440, 165.0, True, True)}
    backend = SimulationColorBackend()
    coordinator = ActivationCoordinator(settings, ProfileService(settings), backend, lambda: displays)

    coordinator.on_foreground(ForegroundProcess(1, "escapefromtarkov.exe", "EFT"))
    assert coordinator.active_profile_id == "eft"
    coordinator.on_foreground(ForegroundProcess(2, "explorer.exe", "Desktop"))

    assert coordinator.active_profile_id == "global"
    assert backend.applied[-1] == ("D1", settings.profiles[0].visual)


def test_disabling_active_specific_profile_falls_back_to_global_on_refresh():
    settings = AppSettings(
        global_enabled=True,
        profiles=[
            GameProfile(id="global", name="Global", builtin_id="global", processes=[], display_ids=["D1"]),
            GameProfile(id="eft", name="EFT", processes=["escapefromtarkov.exe"], display_ids=["D1"]),
        ],
    )
    displays = {"D1": DisplayInfo("D1", "Main", 2560, 1440, 165.0, True, True)}
    backend = SimulationColorBackend()
    coordinator = ActivationCoordinator(settings, ProfileService(settings), backend, lambda: displays)
    coordinator.on_foreground(ForegroundProcess(1, "escapefromtarkov.exe", "EFT"))
    settings.profiles[1].enabled = False

    coordinator.refresh_profile("eft")

    assert coordinator.active_profile_id == "global"
