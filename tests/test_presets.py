from unloop.core.presets import preferences_for_mode
from unloop.domain.models import DiscoveryMode


def test_deep_cut_is_more_adventurous_than_safe() -> None:
    safe = preferences_for_mode(DiscoveryMode.SAFE)
    deep = preferences_for_mode(DiscoveryMode.DEEP_CUT)
    assert deep.discovery_level > safe.discovery_level
    assert deep.minimum_new_artist_ratio > safe.minimum_new_artist_ratio
    assert deep.popularity_ceiling is not None
