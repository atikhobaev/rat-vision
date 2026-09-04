from ratvision.domain.models import AppSettings


def test_analytics_defaults_to_enabled_without_precreated_identity():
    settings=AppSettings()
    assert settings.analytics_enabled is True
    assert settings.analytics_install_id is None
    assert settings.analytics_last_daily_active is None
