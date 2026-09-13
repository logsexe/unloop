from datetime import UTC, datetime, timedelta

from unloop.domain.models import ArtistCooldown, FeedbackAction, FeedbackEvent
from unloop.storage.sqlite import SQLiteStore


def test_cooldown_round_trip(tmp_path) -> None:
    store = SQLiteStore(tmp_path / "unloop.db")
    now = datetime.now(UTC)
    store.set_artist_cooldown(
        ArtistCooldown(
            artist_id="artist-1",
            artist_name="Artist One",
            until=now + timedelta(days=90),
            created_at=now,
        )
    )
    active = store.active_cooldowns(now=now)
    assert len(active) == 1
    assert active[0].artist_id == "artist-1"


def test_feedback_is_local_and_explicit(tmp_path) -> None:
    store = SQLiteStore(tmp_path / "unloop.db")
    event = FeedbackEvent(
        track_id="track-1",
        artist_id="artist-1",
        action=FeedbackAction.LIKE,
        created_at=datetime.now(UTC),
    )
    store.record_feedback(event)
    assert store.recent_feedback()[0].action is FeedbackAction.LIKE
