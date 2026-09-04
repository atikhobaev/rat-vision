from __future__ import annotations

# RAT VISION migration compatibility code, 2026-09-03.
# This module recognizes settings produced by incheon-kim/tarkov-settings;
# see LICENSE and LICENSES.md (LGPL-2.1 and attribution details).

from typing import Any

from ratvision.domain.models import normalize_executable

CURRENT_SCHEMA_VERSION = 1


def is_current_payload(payload: dict[str, Any]) -> bool:
    return payload.get("schema_version") == CURRENT_SCHEMA_VERSION and "profiles" in payload


def migrate_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if is_current_payload(payload):
        migrated = dict(payload)
        app = dict(payload.get("app") or {})
        app.setdefault("analytics_enabled", True)
        migrated["app"] = app
        return migrated

    if any(key in payload for key in ("brightness", "contrast", "gamma", "saturation", "pTargets")):
        processes = []
        for value in payload.get("pTargets") or []:
            normalized = normalize_executable(str(value))
            if normalized and not normalized.endswith(".exe"):
                normalized += ".exe"
            if normalized not in processes:
                processes.append(normalized)
        display = payload.get("display")
        return {
            "schema_version": CURRENT_SCHEMA_VERSION,
            "app": {
                "global_enabled": True,
                "theme": "night",
                "launch_with_windows": False,
                "start_minimized": bool(payload.get("minimizeOnStart", False)),
                "close_to_tray": True,
                "always_on_top": False,
                "analytics_enabled": True,
            },
            "profiles": [
                {
                    "id": "imported-upstream",
                    "name": "Imported profile",
                    "emoji": "🐀",
                    "enabled": True,
                    "processes": processes,
                    "display_ids": [str(display)] if display else [],
                    "visual": {
                        "brightness": float(payload.get("brightness", 0.5)),
                        "contrast": float(payload.get("contrast", 0.5)),
                        "gamma": float(payload.get("gamma", 1.0)),
                        "saturation": int(payload.get("saturation", 0)),
                    },
                    "builtin_id": None,
                }
            ],
        }

    return {
        "schema_version": CURRENT_SCHEMA_VERSION,
        "app": {"analytics_enabled": True},
        "profiles": [],
    }
