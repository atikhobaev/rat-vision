from ratvision.domain.defaults import create_default_profiles
from ratvision.domain.models import DisplayInfo


def test_default_profiles_include_three_games_and_primary_display():
    displays = [DisplayInfo("DISPLAY1", "Main", 2560, 1440, 165.0, True, True)]
    profiles = create_default_profiles(displays)
    assert [p.name for p in profiles] == [
        "Global",
        "Escape from Tarkov",
        "Escape from Tarkov: Arena",
        "Hunt: Showdown",
    ]
    assert profiles[1].processes == ["escapefromtarkov.exe"]
    assert set(profiles[3].processes) == {"hunt.exe", "huntgame.exe"}
    assert all(p.display_ids == ["DISPLAY1"] for p in profiles)


def test_default_profiles_choose_first_online_display_when_no_primary():
    displays = [
        DisplayInfo("DISPLAY1", "Offline", 1920, 1080, 60.0, False, False),
        DisplayInfo("DISPLAY2", "Second", 2560, 1440, 144.0, False, True),
    ]
    profiles = create_default_profiles(displays)
    assert all(p.display_ids == ["DISPLAY2"] for p in profiles)


def test_default_profiles_include_global_profile_first():
    displays = [DisplayInfo("DISPLAY1", "Main", 2560, 1440, 165.0, True, True)]
    profiles = create_default_profiles(displays)
    global_profile = profiles[0]
    assert global_profile.builtin_id == "global"
    assert global_profile.name == "Global"
    assert global_profile.emoji == "🌐"
    assert global_profile.processes == []
    assert global_profile.display_ids == ["DISPLAY1"]
