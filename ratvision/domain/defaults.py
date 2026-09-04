from __future__ import annotations

from collections.abc import Sequence

from .models import DisplayInfo, GameProfile, VisualParameters


def _default_display_ids(displays: Sequence[DisplayInfo]) -> list[str]:
    for display in displays:
        if display.primary and display.online:
            return [display.id]
    for display in displays:
        if display.online:
            return [display.id]
    return []


def create_global_profile(displays: Sequence[DisplayInfo]) -> GameProfile:
    return GameProfile(
        name="Global",
        emoji="🌐",
        processes=[],
        display_ids=_default_display_ids(displays),
        visual=VisualParameters(),
        builtin_id="global",
    )


def ensure_global_profile(profiles: list[GameProfile], displays: Sequence[DisplayInfo]) -> list[GameProfile]:
    global_profile = next((profile for profile in profiles if profile.builtin_id == "global"), None)
    if global_profile is None:
        global_profile = create_global_profile(displays)
        profiles.insert(0, global_profile)
    elif profiles and profiles[0] is not global_profile:
        profiles.remove(global_profile)
        profiles.insert(0, global_profile)
    return profiles


def create_default_profiles(displays: Sequence[DisplayInfo]) -> list[GameProfile]:
    target_displays = _default_display_ids(displays)
    common = VisualParameters()
    return [
        create_global_profile(displays),
        GameProfile(
            name="Escape from Tarkov",
            emoji="🐀",
            processes=["EscapeFromTarkov.exe"],
            display_ids=target_displays.copy(),
            visual=common,
            builtin_id="eft",
        ),
        GameProfile(
            name="Escape from Tarkov: Arena",
            emoji="⚔️",
            processes=["EscapeFromTarkovArena.exe"],
            display_ids=target_displays.copy(),
            visual=common,
            builtin_id="eft-arena",
        ),
        GameProfile(
            name="Hunt: Showdown",
            emoji="🤠",
            processes=["hunt.exe", "HuntGame.exe"],
            display_ids=target_displays.copy(),
            visual=common,
            builtin_id="hunt-showdown",
        ),
    ]
