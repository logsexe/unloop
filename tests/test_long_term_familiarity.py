from datetime import UTC, datetime

from unloop.core.scoring import DiscoveryScorer
from unloop.domain.models import Candidate, Provider, Track


def _candidate(track_id: str, artist_id: str, known: bool, saturation: float = 0.0) -> Candidate:
    return Candidate(
        track=Track(
            id=track_id,
            title=track_id,
            artist_id=artist_id,
            artist_name=artist_id,
            provider=Provider.SPOTIFY,
            genres=("electronic",),
        ),
        taste_similarity=0.8,
        artist_known=known,
        artist_saturation=saturation,
    )


def test_known_artist_is_not_explained_as_new_without_recent_history() -> None:
    scorer = DiscoveryScorer(discovery_level=80)
    ranked = scorer.rank([_candidate("t1", "familiar", True)], [], limit=1, now=datetime.now(UTC))
    assert "New artist" not in ranked[0].reasons
    assert ranked[0].score.artist_unfamiliarity <= 0.2


def test_saturated_artist_scores_below_equivalent_new_artist() -> None:
    scorer = DiscoveryScorer(discovery_level=80)
    ranked = scorer.rank(
        [
            _candidate("new", "new-artist", False, 0.0),
            _candidate("old", "old-artist", True, 0.9),
        ],
        [],
        limit=2,
        now=datetime.now(UTC),
    )
    scores = {item.track.id: item.score.final_score for item in ranked}
    assert scores["new"] > scores["old"]
