from __future__ import annotations

from datetime import UTC, datetime

import pytest

from unloop.domain.models import Candidate, Listen, Provider, Track
from unloop.providers.base import CandidateProvider
from unloop.providers.composite import CompositeCandidateProvider


class StaticProvider(CandidateProvider):
    def __init__(self, candidates: list[Candidate]) -> None:
        self.items = candidates

    async def candidates(self, history: list[Listen], limit: int = 200) -> list[Candidate]:
        return self.items[:limit]


@pytest.mark.asyncio
async def test_composite_prefers_higher_confidence_duplicate() -> None:
    track = Track(id="1", title="Song", artist_id="a", artist_name="Artist", provider=Provider.SPOTIFY)
    low = Candidate(track=track, source_confidence=0.5, source="spotify")
    high = Candidate(track=track, source_confidence=0.9, source="listenbrainz-cf")
    history = [Listen(track=track.model_copy(update={"id": "heard"}), played_at=datetime.now(UTC))]
    provider = CompositeCandidateProvider([StaticProvider([low]), StaticProvider([high])])
    result = await provider.candidates(history)
    assert len(result) == 1
    assert result[0].source == "listenbrainz-cf"
