from __future__ import annotations

from dataclasses import dataclass

from unloop.domain.models import DiscoveryMode, DiscoveryPreferences


@dataclass(frozen=True, slots=True)
class PresetDescription:
    mode: DiscoveryMode
    title: str
    description: str
    preferences: DiscoveryPreferences


PRESETS: dict[DiscoveryMode, PresetDescription] = {
    DiscoveryMode.SAFE: PresetDescription(
        mode=DiscoveryMode.SAFE,
        title="Safe",
        description="Mostly familiar territory, but with fresh tracks and artists.",
        preferences=DiscoveryPreferences(
            mode=DiscoveryMode.SAFE,
            discovery_level=40,
            minimum_new_artist_ratio=0.45,
            max_tracks_per_artist=2,
        ),
    ),
    DiscoveryMode.EXPLORE: PresetDescription(
        mode=DiscoveryMode.EXPLORE,
        title="Explore",
        description="Adjacent genres and scenes with a strong bias toward new artists.",
        preferences=DiscoveryPreferences(
            mode=DiscoveryMode.EXPLORE,
            discovery_level=70,
            minimum_new_artist_ratio=0.70,
            max_tracks_per_artist=1,
        ),
    ),
    DiscoveryMode.DEEP_CUT: PresetDescription(
        mode=DiscoveryMode.DEEP_CUT,
        title="Deep Cut",
        description="Lower-exposure artists and less obvious tracks within your taste graph.",
        preferences=DiscoveryPreferences(
            mode=DiscoveryMode.DEEP_CUT,
            discovery_level=85,
            minimum_new_artist_ratio=0.80,
            max_tracks_per_artist=1,
            popularity_ceiling=0.55,
        ),
    ),
    DiscoveryMode.CHAOS: PresetDescription(
        mode=DiscoveryMode.CHAOS,
        title="Chaos",
        description="Maximum exploration with deliberately wider genre and artist distance.",
        preferences=DiscoveryPreferences(
            mode=DiscoveryMode.CHAOS,
            discovery_level=100,
            minimum_new_artist_ratio=0.90,
            max_tracks_per_artist=1,
            popularity_ceiling=0.70,
        ),
    ),
}


def preferences_for_mode(mode: DiscoveryMode) -> DiscoveryPreferences:
    if mode is DiscoveryMode.CUSTOM:
        return DiscoveryPreferences(mode=mode)
    return PRESETS[mode].preferences.model_copy(deep=True)
