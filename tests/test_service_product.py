from datetime import UTC, datetime
from pathlib import Path

import pytest

from unloop.core.service import DiscoveryService
from unloop.domain.models import Candidate, Listen, Provider, Track
from unloop.providers.base import CandidateProvider, HistoryProvider, PlaylistProvider
from unloop.storage import SQLiteStore


class History(HistoryProvider):
    async def recent_listens(self, limit: int = 250) -> list[Listen]:
        return []


class Candidates(CandidateProvider):
    async def candidates(self, history: list[Listen], limit: int = 200) -> list[Candidate]:
        return [Candidate(track=Track(id="t1", title="Fresh", artist_id="a1", artist_name="New", provider=Provider.LOCAL), taste_similarity=0.9)]


class Playlists(PlaylistProvider):
    def __init__(self) -> None:
        self.name = ""

    async def publish_playlist(self, name: str, tracks):  # type: ignore[no-untyped-def]
        self.name = name
        return "https://example.test/playlist"


@pytest.mark.asyncio
async def test_generate_records_recommendation_memory(tmp_path: Path) -> None:
    store = SQLiteStore(tmp_path / "u.db")
    service = DiscoveryService(History(), Candidates(), Playlists(), store=store)
    ranked = await service.generate(70, limit=1)
    assert ranked
    assert "t1" in store.recommended_track_ids()


@pytest.mark.asyncio
async def test_custom_and_default_playlist_names(tmp_path: Path) -> None:
    custom_provider = Playlists()
    service = DiscoveryService(History(), Candidates(), custom_provider, store=SQLiteStore(tmp_path / "custom.db"))
    await service.publish(70, limit=1, playlist_name="Electronic Reset")
    assert custom_provider.name == "Electronic Reset"

    default_provider = Playlists()
    service = DiscoveryService(History(), Candidates(), default_provider, store=SQLiteStore(tmp_path / "default.db"))
    await service.publish(70, limit=1, playlist_name="   ")
    assert default_provider.name == "UNLOOP Discovery"
