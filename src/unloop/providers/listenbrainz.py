from __future__ import annotations

from typing import Any

from unloop.domain.models import Candidate, Listen
from unloop.integrations.listenbrainz import ListenBrainzAPI
from unloop.integrations.spotify.client import SpotifyAPI
from unloop.providers.base import CandidateProvider


class ListenBrainzCandidateProvider(CandidateProvider):
    """Resolve open ListenBrainz collaborative-filtering picks into Spotify playback items."""

    def __init__(self, listenbrainz: ListenBrainzAPI, spotify: SpotifyAPI, username: str) -> None:
        self.listenbrainz = listenbrainz
        self.spotify = spotify
        self.username = username

    async def candidates(self, history: list[Listen], limit: int = 200) -> list[Candidate]:
        raw_recs = await self.listenbrainz.recommendations(self.username, count=min(limit, 100))
        if not raw_recs:
            return []
        mbids = [str(item.get("recording_mbid") or "") for item in raw_recs if item.get("recording_mbid")]
        metadata = await self.listenbrainz.recording_metadata(mbids)
        heard_ids = {item.track.id for item in history}
        scores = [float(item.get("score") or 0) for item in raw_recs]
        low, high = (min(scores), max(scores)) if scores else (0.0, 1.0)
        span = max(high - low, 0.0001)
        result: list[Candidate] = []

        for rec in raw_recs:
            mbid = str(rec.get("recording_mbid") or "")
            info = metadata.get(mbid) or {}
            title, artist = self._names(info)
            if not title or not artist:
                continue
            query = f'track:"{title}" artist:"{artist}"'
            try:
                matches = await self.spotify.search_tracks(query, limit=5)
            except Exception:
                continue
            match = self._best_match(matches, title, artist)
            if not match:
                continue
            track = self.spotify.track_from_raw(match, genres=self._tags(info))
            if track.id in heard_ids:
                continue
            track.musicbrainz_recording_id = mbid
            raw_score = float(rec.get("score") or 0)
            community = 0.60 + 0.35 * ((raw_score - low) / span)
            result.append(
                Candidate(
                    track=track,
                    taste_similarity=0.70,
                    community_similarity=min(0.95, community),
                    source_confidence=0.86,
                    artist_known=False,
                    source="listenbrainz-cf",
                )
            )
            if len(result) >= limit:
                break
        return result

    @staticmethod
    def _names(info: dict[str, Any]) -> tuple[str, str]:
        title = str(info.get("recording_name") or info.get("name") or "").strip()
        artist = str(info.get("artist_credit_name") or "").strip()
        if not artist:
            artists = info.get("artist") or info.get("artists") or []
            if isinstance(artists, list) and artists:
                first = artists[0] if isinstance(artists[0], dict) else {}
                artist = str(first.get("name") or first.get("artist_name") or "").strip()
        return title, artist

    @staticmethod
    def _tags(info: dict[str, Any]) -> tuple[str, ...]:
        tag_block = info.get("tag") or {}
        tags = tag_block.get("recording") if isinstance(tag_block, dict) else []
        if not isinstance(tags, list):
            return ()
        ordered = sorted(
            (item for item in tags if isinstance(item, dict) and item.get("tag")),
            key=lambda item: int(item.get("count") or 0),
            reverse=True,
        )
        return tuple(str(item["tag"]) for item in ordered[:8])

    @staticmethod
    def _best_match(items: list[dict[str, Any]], title: str, artist: str) -> dict[str, Any] | None:
        t, a = title.casefold(), artist.casefold()
        for item in items:
            item_title = str(item.get("name") or "").casefold()
            artists = item.get("artists") or []
            item_artist = str((artists[0] if artists else {}).get("name") or "").casefold()
            if item_title == t and item_artist == a:
                return item
        return items[0] if items else None
