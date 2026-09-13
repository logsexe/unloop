from __future__ import annotations

from collections import Counter

from unloop.core.taste import calculate_artist_saturation
from unloop.domain.models import Candidate, Listen, RankedTrack
from unloop.integrations.spotify.client import SpotifyAPI
from unloop.providers.base import CandidateProvider, HistoryProvider, PlaylistProvider
from unloop.storage import SQLiteStore


class SpotifyProvider(HistoryProvider, CandidateProvider, PlaylistProvider):
    """Spotify adapter for personal Development Mode use.

    Spotify supplies taste/history and playback destination. UNLOOP owns ranking.
    Candidate generation deliberately uses catalog search rather than Spotify's
    own recommendation ranking so we can control repetition and diversity.
    """

    def __init__(
        self,
        api: SpotifyAPI,
        store: SQLiteStore | None = None,
        seed_genres: tuple[str, ...] = (),
    ) -> None:
        self.api = api
        self.store = store
        self.seed_genres = tuple(g.strip() for g in seed_genres if g.strip())
        self._top_artists_cache: list[dict[str, object]] | None = None

    async def recent_listens(self, limit: int = 250) -> list[Listen]:
        listens = await self.api.recently_played(limit=limit)
        artist_genres = await self._artist_genres()
        enriched: list[Listen] = []
        for listen in listens:
            genres = artist_genres.get(listen.track.artist_id, ())
            if genres:
                listen.track.genres = genres
            enriched.append(listen)
        return enriched

    async def candidates(self, history: list[Listen], limit: int = 200) -> list[Candidate]:
        artists = await self._top_artists()
        artist_genres = await self._artist_genres()
        genre_counts: Counter[str] = Counter()
        top_artist_ids: set[str] = set()
        for artist in artists:
            artist_id = artist.get("id")
            if artist_id:
                artist_key = str(artist_id)
                top_artist_ids.add(artist_key)
                genre_counts.update(artist_genres.get(artist_key, ()))

        top_tracks = await self.top_tracks_raw(limit=50)
        recent_counts = Counter(item.track.artist_id for item in history)
        recent_names = {item.track.artist_id: item.track.artist_name for item in history}
        for artist in artists:
            if artist.get("id") and artist.get("name"):
                recent_names.setdefault(str(artist["id"]), str(artist["name"]))
        top_track_counts = Counter(
            str(((item.get("artists") or [{}])[0]).get("id") or "")
            for item in top_tracks
            if ((item.get("artists") or [{}])[0]).get("id")
        )
        top_artist_ranks = {
            str(artist["id"]): index + 1
            for index, artist in enumerate(artists)
            if artist.get("id")
        }
        saturation = {
            item.artist_id: item.score / 100
            for item in calculate_artist_saturation(
                recent_artist_counts=recent_counts,
                recent_artist_names=recent_names,
                top_track_artist_counts=top_track_counts,
                top_artist_ranks=top_artist_ranks,
                limit=max(50, len(top_artist_ranks)),
            )
        }

        # Include genres observed in recent history after enrichment.
        for listen in history:
            genre_counts.update(listen.track.genres)

        top_genres = list(dict.fromkeys([*self.seed_genres, *[genre for genre, _ in genre_counts.most_common(8)]]))
        if not top_genres:
            # Search still functions for accounts where Spotify does not expose genres.
            top_genres = ["indie", "electronic", "alternative", "rock", "pop"]

        heard_track_ids = {listen.track.id for listen in history}
        candidates: dict[str, Candidate] = {}

        for genre_rank, genre in enumerate(top_genres):
            if len(candidates) >= limit:
                break
            # One broad taste-adjacent query and one deliberately lower-exposure query.
            queries = (f'genre:"{genre}"', f'genre:"{genre}" tag:hipster')
            for query_index, query in enumerate(queries):
                try:
                    raw_tracks = await self.api.search_tracks(query, limit=10)
                except Exception:
                    # `tag:hipster` can vary by catalog/market. Broad genre search is enough
                    # to keep a batch usable if the narrower query fails.
                    if query_index == 1:
                        continue
                    raise
                for raw in raw_tracks:
                    track_id = raw.get("id")
                    if not track_id or track_id in heard_track_ids or track_id in candidates:
                        continue
                    track = self.api.track_from_raw(raw, genres=(genre,))
                    # Genre rank is a transparent affinity proxy. Existing top artists are
                    # allowed into SAFE mode but rank below genuinely new artists in EXPLORE+.
                    base_taste = max(0.62, 0.94 - genre_rank * 0.04)
                    if track.artist_id in top_artist_ids:
                        base_taste = min(0.98, base_taste + 0.03)
                    candidates[track.id] = Candidate(
                        track=track,
                        taste_similarity=base_taste,
                        community_similarity=0.5,
                        source_confidence=0.78 if query_index == 0 else 0.72,
                        artist_known=track.artist_id in top_artist_ids,
                        artist_saturation=saturation.get(track.artist_id, 0.0),
                        source=f"spotify-search:{'deep-cut' if query_index else 'genre'}:{genre}",
                    )
                    if len(candidates) >= limit:
                        break
                if len(candidates) >= limit:
                    break

        return list(candidates.values())[:limit]

    async def publish_playlist(self, name: str, tracks: list[RankedTrack]) -> str:
        return await self.api.create_private_playlist(
            name=name,
            description=(
                "Generated by UNLOOP — open-source music discovery optimized for novelty, "
                "not engagement. No ads, sponsored placement, or paid ranking."
            ),
            tracks=tracks,
        )

    async def taste_summary(self) -> dict[str, object]:
        artists = await self._top_artists()
        tracks = await self.api.top_items("tracks", "medium_term", 20)
        cached = (
            {item.provider_artist_id: item for item in self.store.artist_metadata_many(
                [str(a.get("id")) for a in artists if a.get("id")]
            )}
            if self.store else {}
        )
        genre_counts: Counter[str] = Counter()
        for artist in artists:
            artist_id = str(artist.get("id") or "")
            genres = tuple(str(g) for g in artist.get("genres") or [])
            metadata = cached.get(artist_id)
            if metadata:
                genres = metadata.genres or tuple(metadata.tags) or genres
            genre_counts.update(genres)
        return {
            "top_genres": [
                {"name": genre, "weight": count}
                for genre, count in genre_counts.most_common(15)
            ],
            "top_artists": [
                {
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "genres": list((cached.get(str(item.get("id"))) or None).genres)
                        if cached.get(str(item.get("id"))) else (item.get("genres") or []),
                    "musicbrainz_artist_id": (cached.get(str(item.get("id"))) or None).musicbrainz_artist_id
                        if cached.get(str(item.get("id"))) else None,
                }
                for item in artists[:20]
            ],
            "top_tracks": [
                {
                    "id": item.get("id"),
                    "name": item.get("name"),
                    "artist": ((item.get("artists") or [{}])[0]).get("name"),
                }
                for item in tracks
            ],
        }

    async def _top_artists(self) -> list[dict[str, object]]:
        if self._top_artists_cache is None:
            merged: dict[str, dict[str, object]] = {}
            for time_range in ("short_term", "medium_term", "long_term"):
                for artist in await self.api.top_items("artists", time_range, 50):
                    artist_id = artist.get("id")
                    if artist_id and str(artist_id) not in merged:
                        merged[str(artist_id)] = artist
            self._top_artists_cache = list(merged.values())
        return self._top_artists_cache

    async def _artist_genres(self) -> dict[str, tuple[str, ...]]:
        artists = await self._top_artists()
        result = {
            str(artist["id"]): tuple(str(g) for g in artist.get("genres") or [])
            for artist in artists
            if artist.get("id")
        }
        if self.store:
            for metadata in self.store.artist_metadata_many(list(result)):
                if metadata.genres:
                    result[metadata.provider_artist_id] = metadata.genres
                elif metadata.tags:
                    result[metadata.provider_artist_id] = tuple(metadata.tags)
        return result

    async def top_artists_raw(self) -> list[dict[str, object]]:
        return await self._top_artists()

    async def top_tracks_raw(self, limit: int = 50) -> list[dict[str, object]]:
        return await self.api.top_items("tracks", "medium_term", limit)
