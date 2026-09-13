from __future__ import annotations

from unloop.core.scoring import DiscoveryScorer
from datetime import UTC, datetime
from uuid import uuid4

from unloop.domain.models import DiscoveryMode, DiscoveryPreferences, RankedTrack, RecommendationRecord
from unloop.providers.base import CandidateProvider, HistoryProvider, PlaylistProvider
from unloop.storage import SQLiteStore


class DiscoveryService:
    def __init__(
        self,
        history_provider: HistoryProvider,
        candidate_provider: CandidateProvider,
        playlist_provider: PlaylistProvider,
        store: SQLiteStore | None = None,
    ) -> None:
        self.history_provider = history_provider
        self.candidate_provider = candidate_provider
        self.playlist_provider = playlist_provider
        self.store = store

    async def generate(
        self,
        discovery_level: int,
        limit: int = 30,
        preferences: DiscoveryPreferences | None = None,
    ) -> list[RankedTrack]:
        history = await self.history_provider.recent_listens()
        candidates = await self.candidate_provider.candidates(history)
        heard_track_ids = {item.track.id for item in history}
        heard_artist_ids = {item.track.artist_id for item in history}
        preferences = preferences or DiscoveryPreferences(discovery_level=discovery_level)
        cooldowns = self.store.active_cooldowns() if self.store else []
        recommended = self.store.recommended_track_ids() if self.store else set()
        liked_artists: set[str] = set()
        disliked_artists: set[str] = set()
        rejected_tracks: set[str] = set()
        if self.store:
            liked_artists, disliked_artists, rejected_tracks = self.store.feedback_bias()
        scorer = DiscoveryScorer(
            discovery_level=discovery_level,
            preferences=preferences,
        )
        ranked = scorer.rank(
            candidates,
            history,
            limit=limit,
            cooldown_artist_ids={item.artist_id for item in cooldowns},
            previously_recommended_track_ids=recommended,
            liked_artist_ids=liked_artists,
            disliked_artist_ids=disliked_artists,
            rejected_track_ids=rejected_tracks,
        )
        if self.store and ranked:
            batch_id = uuid4().hex[:12]
            created_at = datetime.now(UTC)
            self.store.record_recommendation_batch(
                batch_id=batch_id,
                created_at=created_at,
                mode=preferences.mode if preferences else DiscoveryMode.EXPLORE,
                discovery_level=discovery_level,
                records=[RecommendationRecord(
                    batch_id=batch_id,
                    track_id=item.track.id,
                    artist_id=item.track.artist_id,
                    source=item.source,
                    final_score=item.score.final_score,
                    recommended_at=created_at,
                    is_new_track=item.track.id not in heard_track_ids,
                    is_new_artist=item.track.artist_id not in heard_artist_ids,
                ) for item in ranked],
            )
        return ranked

    async def publish(
        self,
        discovery_level: int,
        limit: int = 30,
        preferences: DiscoveryPreferences | None = None,
        playlist_name: str | None = None,
    ) -> tuple[str, list[RankedTrack]]:
        ranked = await self.generate(
            discovery_level=discovery_level,
            limit=limit,
            preferences=preferences,
        )
        name = (playlist_name or "UNLOOP Discovery").strip() or "UNLOOP Discovery"
        url = await self.playlist_provider.publish_playlist(name, ranked)
        return url, ranked
