from ratvision.domain.models import AppSettings, GameProfile, VisualParameters
from ratvision.domain.profile_service import ProfileService


def make_service():
    settings = AppSettings(
        profiles=[
            GameProfile(
                id="a",
                name="A",
                processes=["GAMEA.EXE"],
                display_ids=["D1"],
                visual=VisualParameters(0.7, 0.6, 1.3, 70),
            ),
            GameProfile(
                id="b",
                name="B",
                processes=["gameb.exe"],
                display_ids=["D2"],
                visual=VisualParameters(),
            ),
        ]
    )
    return ProfileService(settings)


def test_match_is_case_insensitive_and_enabled_only():
    service = make_service()
    assert service.match("GaMeA.ExE").id == "a"
    service.get("a").enabled = False
    assert service.match("gamea.exe") is None


def test_copy_visuals_does_not_copy_processes_or_displays():
    service = make_service()
    target = service.get("b")
    target_processes = list(target.processes)
    target_displays = list(target.display_ids)
    service.copy_visuals("a", "b")
    assert target.processes == target_processes
    assert target.display_ids == target_displays
    assert target.visual == service.get("a").visual


def test_process_and_display_edits_are_normalized_and_unique():
    service = make_service()
    service.add_process("b", r"C:\Games\NEWGAME.EXE")
    service.add_process("b", "newgame.exe")
    service.set_displays("b", ["D2", "D2", "D3"])
    assert service.get("b").processes == ["gameb.exe", "newgame.exe"]
    assert service.get("b").display_ids == ["D2", "D3"]


def test_global_profile_is_found_separately_and_not_by_process_matching():
    settings = AppSettings(
        profiles=[
            GameProfile(id="global", name="Global", builtin_id="global", processes=[], display_ids=["D1"]),
            GameProfile(id="game", name="Game", processes=["game.exe"], display_ids=["D1"]),
        ]
    )
    service = ProfileService(settings)
    assert service.global_profile().id == "global"
    assert service.match("explorer.exe") is None
    assert service.match("game.exe").id == "game"


def test_global_profile_cannot_be_removed():
    settings = AppSettings(
        profiles=[GameProfile(id="global", name="Global", builtin_id="global", processes=[], display_ids=["D1"])]
    )
    service = ProfileService(settings)
    try:
        service.remove_profile("global")
    except ValueError as exc:
        assert "global" in str(exc).lower()
    else:
        raise AssertionError("global profile removal must be rejected")


def test_global_profile_rejects_target_process_addition():
    settings = AppSettings(
        profiles=[GameProfile(id="global", name="Global", builtin_id="global", processes=[], display_ids=["D1"])]
    )
    service = ProfileService(settings)
    try:
        service.add_process("global", "game.exe")
    except ValueError as exc:
        assert "process" in str(exc).lower()
    else:
        raise AssertionError("global profile must remain process-independent")
