from datetime import UTC, datetime

from unloop.core.scoring import DiscoveryScorer
from unloop.domain.models import Candidate, Listen, Provider, Track


def _track(track_id: str, artist_id: str) -> Track:
    return Track(id=track_id, title=track_id, artist_id=artist_id, artist_name=artist_id, provider=Provider.SPOTIFY)


def test_previously_recommended_track_is_excluded() -> None:
    candidates = [Candidate(track=_track("seen", "a1")), Candidate(track=_track("new", "a2"))]
    ranked = DiscoveryScorer().rank(candidates, [], previously_recommended_track_ids={"seen"})
    assert [item.track.id for item in ranked] == ["new"]


def test_explicit_dislike_excludes_artist() -> None:
    candidates = [Candidate(track=_track("t1", "bad")), Candidate(track=_track("t2", "good"))]
    ranked = DiscoveryScorer().rank(candidates, [], disliked_artist_ids={"bad"})
    assert all(item.track.artist_id != "bad" for item in ranked)
