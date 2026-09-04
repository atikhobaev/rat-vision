from pathlib import Path

from ratvision.domain.models import AppSettings, GameProfile, ThemeMode, VisualParameters
from ratvision.persistence.settings_store import SettingsStore


def make_settings() -> AppSettings:
    return AppSettings(
        global_enabled=False,
        theme=ThemeMode.DAY,
        profiles=[
            GameProfile(
                id="global",
                name="Global",
                emoji="🌐",
                enabled=True,
                processes=[],
                display_ids=["DISPLAY1"],
                visual=VisualParameters(),
                builtin_id="global",
            ),
            GameProfile(
                id="p1",
                name="Game",
                emoji="🎮",
                enabled=True,
                processes=["GAME.EXE"],
                display_ids=["DISPLAY1", "DISPLAY2"],
                visual=VisualParameters(0.6, 0.7, 1.2, 55),
            )
        ],
        launch_with_windows=True,
        start_minimized=True,
        always_on_top=True,
    )


def test_settings_round_trip_preserves_profiles(tmp_path: Path):
    store = SettingsStore(tmp_path / "settings.json")
    settings = make_settings()
    store.save(settings)
    assert store.load([]) == settings


def test_invalid_json_is_backed_up_and_defaults_loaded(tmp_path: Path):
    path = tmp_path / "settings.json"
    path.write_text("{broken", encoding="utf-8")
    loaded = SettingsStore(path).load([])
    assert len(loaded.profiles) == 4
    assert list(tmp_path.glob("settings.invalid-*.json"))


def test_export_and_import_round_trip(tmp_path: Path):
    store = SettingsStore(tmp_path / "settings.json")
    exported = tmp_path / "backup.ratvision.json"
    settings = make_settings()
    store.export_to(settings, exported)
    imported = store.import_from(exported, [])
    assert imported == settings


def test_loading_existing_settings_adds_missing_global_profile(tmp_path: Path):
    path = tmp_path / "settings.json"
    path.write_text('''{
  "schema_version": 1,
  "app": {"global_enabled": true, "theme": "night"},
  "profiles": [
    {"id":"p1","name":"Game","emoji":"🎮","enabled":true,"processes":["game.exe"],"display_ids":["DISPLAY1"],"visual":{"brightness":0.5,"contrast":0.5,"gamma":1.0,"saturation":0},"builtin_id":null}
  ]
}\n''', encoding="utf-8")
    displays = []
    loaded = SettingsStore(path).load(displays)
    assert loaded.profiles[0].builtin_id == "global"
    assert loaded.profiles[1].id == "p1"


def test_obsolete_nonfunctional_settings_are_not_written(tmp_path: Path):
    store = SettingsStore(tmp_path / "settings.json")
    settings = make_settings()
    store.save(settings)
    text = (tmp_path / "settings.json").read_text(encoding="utf-8")
    for obsolete in (
        "show_on_profile_activation",
        "notifications_enabled",
        "notify_on_activation",
        "notify_on_errors",
        "subtle_texture",
        "emoji_enabled",
    ):
        assert obsolete not in text


def test_analytics_consent_identity_and_daily_timestamp_round_trip(tmp_path: Path):
    store=SettingsStore(tmp_path/'settings.json')
    settings=make_settings()
    settings.analytics_enabled=True
    settings.analytics_install_id='11111111-1111-4111-8111-111111111111'
    settings.analytics_last_daily_active=1234.5
    store.save(settings)
    loaded=store.load([])
    assert loaded.analytics_enabled is True
    assert loaded.analytics_install_id == settings.analytics_install_id
    assert loaded.analytics_last_daily_active == 1234.5


def test_profile_export_never_contains_analytics_install_identity(tmp_path: Path):
    store=SettingsStore(tmp_path/'settings.json')
    settings=make_settings(); settings.analytics_enabled=True; settings.analytics_install_id='secret-install-id'; settings.analytics_last_daily_active=999.0
    exported=tmp_path/'profiles.json'; store.export_to(settings,exported)
    text=exported.read_text(encoding='utf-8')
    assert 'secret-install-id' not in text
    assert 'analytics_install_id' not in text
    assert 'analytics_last_daily_active' not in text
    assert 'analytics_enabled' not in text
