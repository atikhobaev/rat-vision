from ratvision.persistence.migration import migrate_payload


def test_migrate_upstream_flat_settings_to_single_user_profile():
    payload = {
        "brightness": 0.61,
        "contrast": 0.43,
        "gamma": 1.18,
        "saturation": 72,
        "pTargets": ["EscapeFromTarkov", "CUSTOM.EXE"],
        "display": r"\\.\DISPLAY2",
        "minimizeOnStart": True,
    }
    migrated = migrate_payload(payload)
    assert migrated["schema_version"] == 1
    assert migrated["app"]["start_minimized"] is True
    assert len(migrated["profiles"]) == 1
    profile = migrated["profiles"][0]
    assert profile["name"] == "Imported profile"
    assert profile["processes"] == ["escapefromtarkov.exe", "custom.exe"]
    assert profile["display_ids"] == [r"\\.\DISPLAY2"]
    assert profile["visual"] == {
        "brightness": 0.61,
        "contrast": 0.43,
        "gamma": 1.18,
        "saturation": 72,
    }


def test_existing_schema_without_analytics_defaults_to_enabled():
    migrated=migrate_payload({'schema_version':1,'app':{'global_enabled':True},'profiles':[]})
    assert migrated['app']['analytics_enabled'] is True
