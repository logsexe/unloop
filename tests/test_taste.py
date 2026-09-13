from collections import Counter
from datetime import UTC, datetime

from unloop.core.taste import build_taste_clusters, calculate_artist_saturation
from unloop.domain.models import ArtistMetadata


def test_build_taste_clusters_from_open_metadata() -> None:
    metadata = [
        ArtistMetadata(
            provider_artist_id="a1",
            artist_name="Artist One",
            genres=("house", "electronic"),
            tags={"ambient": 4, "dance": 2},
            updated_at=datetime.now(UTC),
        ),
        ArtistMetadata(
            provider_artist_id="a2",
            artist_name="Artist Two",
            genres=("hip hop",),
            tags={"trap": 3},
            updated_at=datetime.now(UTC),
        ),
    ]
    clusters = build_taste_clusters(metadata)
    assert clusters
    assert clusters[0].name == "Electronic / Dance"
    assert abs(sum(item.weight for item in clusters) - 1.0) < 0.01


def test_artist_saturation_combines_recent_and_long_term_signals() -> None:
    saturation = calculate_artist_saturation(
        recent_artist_counts=Counter({"a1": 6, "a2": 1}),
        recent_artist_names={"a1": "Repeated Artist", "a2": "Other Artist"},
        top_track_artist_counts=Counter({"a1": 4}),
        top_artist_ranks={"a1": 1, "a2": 15},
    )
    assert saturation[0].artist_id == "a1"
    assert saturation[0].score >= 70
    assert saturation[0].status == "saturated"
