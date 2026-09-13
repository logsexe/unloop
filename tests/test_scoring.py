from datetime import UTC, datetime, timedelta

from unloop.core.scoring import DiscoveryScorer
from unloop.domain.models import Candidate, Listen, Provider, Track


def track(track_id: str, artist_id: str, genre: str = "indie") -> Track:
    return Track(
        id=track_id,
        title=track_id,
        artist_id=artist_id,
        artist_name=artist_id,
        provider=Provider.LOCAL,
        genres=(genre,),
    )


def test_unheard_track_beats_heavily_repeated_track_at_high_discovery() -> None:
    now = datetime.now(UTC)
    repeated = track("repeat", "repeat-artist")
    unseen = track("new", "new-artist", "shoegaze")

    history = [
        Listen(track=repeated, played_at=now - timedelta(days=i))
        for i in range(10)
    ]
    candidates = [
        Candidate(track=repeated, taste_similarity=1.0, community_similarity=1.0),
        Candidate(track=unseen, taste_similarity=0.72, community_similarity=0.70),
    ]

    ranked = DiscoveryScorer(discovery_level=90).rank(candidates, history, now=now)

    assert ranked[0].track.id == "new"
    assert "Never played before" in ranked[0].reasons
    assert "New artist" in ranked[0].reasons


def test_discovery_level_is_validated() -> None:
    try:
        DiscoveryScorer(discovery_level=101)
    except ValueError as exc:
        assert "between 0 and 100" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
