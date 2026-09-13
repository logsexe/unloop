from __future__ import annotations

from datetime import UTC, datetime, timedelta

from unloop.domain.models import Candidate, Listen, Provider, RankedTrack, Track
from unloop.providers.base import CandidateProvider, HistoryProvider, PlaylistProvider


class MockProvider(HistoryProvider, CandidateProvider, PlaylistProvider):
    """Offline provider used for local development and CI."""

    async def recent_listens(self, limit: int = 250) -> list[Listen]:
        now = datetime.now(UTC)
        familiar = Track(
            id="familiar-01",
            title="The Familiar Loop",
            artist_id="artist-repeat",
            artist_name="Repeat Artist",
            provider=Provider.LOCAL,
            genres=("indie",),
        )
        return [
            Listen(track=familiar, played_at=now - timedelta(days=i))
            for i in range(min(12, limit))
        ]

    async def candidates(self, history: list[Listen], limit: int = 200) -> list[Candidate]:
        tracks = [
            Candidate(
                track=Track(
                    id="new-01",
                    title="Unknown Signal",
                    artist_id="artist-new-a",
                    artist_name="New Artist A",
                    provider=Provider.LOCAL,
                    genres=("indie", "shoegaze"),
                ),
                taste_similarity=0.82,
                community_similarity=0.78,
            ),
            Candidate(
                track=Track(
                    id="new-02",
                    title="Different Frequency",
                    artist_id="artist-new-b",
                    artist_name="New Artist B",
                    provider=Provider.LOCAL,
                    genres=("ambient techno",),
                ),
                taste_similarity=0.69,
                community_similarity=0.73,
            ),
            Candidate(
                track=Track(
                    id="familiar-01",
                    title="The Familiar Loop",
                    artist_id="artist-repeat",
                    artist_name="Repeat Artist",
                    provider=Provider.LOCAL,
                    genres=("indie",),
                ),
                taste_similarity=0.98,
                community_similarity=0.96,
            ),
        ]
        return tracks[:limit]

    async def publish_playlist(self, name: str, tracks: list[RankedTrack]) -> str:
        return f"local://playlist/{name.lower().replace(' ', '-')}?tracks={len(tracks)}"
