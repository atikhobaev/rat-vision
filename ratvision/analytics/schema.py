from __future__ import annotations

_ALLOWED={
    'app_started': {'app_version','edition','windows_version','gpu_vendor','monitor_count'},
    'daily_active': {'app_version','edition','windows_version'},
    'profile_created': set(),
    'global_profile_enabled': set(),
    'update_installed': {'from_version','to_version'},
    'tutorial_completed': set(),
}

def sanitize_properties(event: str, properties: dict[str, object]) -> dict[str, object]:
    allowed=_ALLOWED.get(event,set())
    return {
        k: v for k, v in properties.items()
        if k in allowed and isinstance(v, (str, int, float, bool))
    }
