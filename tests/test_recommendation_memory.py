from datetime import UTC, datetime
from pathlib import Path

from unloop.domain.models import DiscoveryMode, FeedbackAction, FeedbackEvent, RecommendationRecord
from unloop.storage.sqlite import SQLiteStore


def test_recommendation_memory_and_feedback(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "u.db")
    now = datetime.now(UTC)
    store.record_recommendation_batch(
        "batch1", now, DiscoveryMode.EXPLORE, 70,
        [RecommendationRecord(batch_id="batch1", track_id="t1", artist_id="a1", source="listenbrainz-cf", final_score=0.9, recommended_at=now)],
    )
    assert "t1" in store.recommended_track_ids()
    event = FeedbackEvent(track_id="t1", artist_id="a1", action=FeedbackAction.LIKE, created_at=now)
    store.record_feedback(event)
    store.apply_feedback_to_recommendations(event)
    analytics = store.batch_analytics()
    assert analytics[0].liked == 1
    assert analytics[0].hit_rate == 1.0
