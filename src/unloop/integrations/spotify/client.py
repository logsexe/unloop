from __future__ import annotations

from datetime import datetime
from typing import Any

import httpx

from unloop.core.language import guess_track_language
from unloop.domain.models import Listen, Provider, RankedTrack, Track


class SpotifyQuotaError(RuntimeError):
    pass


class SpotifyRateLimitError(RuntimeError):
    pass


class SpotifyAPI:
    BASE_URL = "https://api.spotify.com/v1"

    def __init__(self, access_token: str, client: httpx.AsyncClient | None = None) -> None:
        self.access_token = access_token
        self._client = client

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {self.access_token}"}
        url = f"{self.BASE_URL}{path}"
        if self._client:
            response = await self._client.request(method, url, headers=headers, params=params, json=json)
            if response.status_code == 429:
                payload = response.json() if response.content else {}
                reason = str(payload.get("reason") or payload.get("error", {}).get("reason") or "")
                if reason == "QUOTA_EXCEEDED":
                    raise SpotifyQuotaError("Spotify Development Mode quota exceeded")
                raise SpotifyRateLimitError("Spotify rate limit exceeded")
            if response.status_code == 429:
                payload = response.json() if response.content else {}
                reason = str(payload.get("reason") or payload.get("error", {}).get("reason") or "")
                if reason == "QUOTA_EXCEEDED":
                    raise SpotifyQuotaError("Spotify Development Mode quota exceeded")
                raise SpotifyRateLimitError("Spotify rate limit exceeded")
            response.raise_for_status()
            return dict(response.json()) if response.content else {}
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.request(method, url, headers=headers, params=params, json=json)
            response.raise_for_status()
            return dict(response.json()) if response.content else {}

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        return await self._request("GET", path, params=params)

    async def _post(self, path: str, json: dict[str, Any]) -> dict[str, Any]:
        return await self._request("POST", path, json=json)

    async def profile(self) -> dict[str, Any]:
        return await self._get("/me")

    async def recently_played(self, limit: int = 200) -> list[Listen]:
        """Fetch multiple cursor pages of recent history.

        Spotify caps each request at 50 items, so UNLOOP walks backwards using
        the `before` cursor until the requested limit is reached.
        """
        requested = max(1, min(limit, 250))
        listens: list[Listen] = []
        before: str | None = None

        while len(listens) < requested:
            page_limit = min(50, requested - len(listens))
            params: dict[str, Any] = {"limit": page_limit}
            if before:
                params["before"] = before
            payload = await self._get("/me/player/recently-played", params)
            items = payload.get("items", [])
            if not items:
                break
            listens.extend(self._listen_from_item(item) for item in items)
            cursor = payload.get("cursors") or {}
            next_before = cursor.get("before")
            if not next_before or next_before == before:
                break
            before = str(next_before)

        return listens[:requested]

    async def top_items(
        self,
        item_type: str = "tracks",
        time_range: str = "medium_term",
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        if item_type not in {"tracks", "artists"}:
            raise ValueError("item_type must be 'tracks' or 'artists'")
        payload = await self._get(
            f"/me/top/{item_type}",
            {"time_range": time_range, "limit": min(limit, 50)},
        )
        return list(payload.get("items", []))

    async def search_tracks(self, query: str, limit: int = 10, offset: int = 0) -> list[dict[str, Any]]:
        # Spotify Development Mode caps search at 10 results per request.
        payload = await self._get(
            "/search",
            {"q": query, "type": "track", "limit": min(limit, 10), "offset": offset},
        )
        tracks = payload.get("tracks") or {}
        return list(tracks.get("items", []))

    async def create_private_playlist(
        self,
        name: str,
        description: str,
        tracks: list[RankedTrack],
    ) -> str:
        playlist = await self._post(
            "/me/playlists",
            {"name": name, "public": False, "description": description},
        )
        playlist_id = playlist["id"]
        uris = [item.track.provider_uri for item in tracks if item.track.provider_uri]
        for start in range(0, len(uris), 100):
            await self._post(f"/playlists/{playlist_id}/items", {"uris": uris[start : start + 100]})
        external = playlist.get("external_urls") or {}
        return str(external.get("spotify") or f"https://open.spotify.com/playlist/{playlist_id}")

    @staticmethod
    def track_from_raw(raw_track: dict[str, Any], genres: tuple[str, ...] = ()) -> Track:
        artists = raw_track.get("artists") or [{}]
        artist = artists[0]
        external_ids = raw_track.get("external_ids") or {}
        album = raw_track.get("album") or {}
        release_date = str(album.get("release_date") or "")
        release_year = int(release_date[:4]) if len(release_date) >= 4 and release_date[:4].isdigit() else None
        # `popularity` is absent in Spotify Development Mode as of 2026.
        popularity_raw = raw_track.get("popularity")
        popularity = popularity_raw / 100 if isinstance(popularity_raw, (int, float)) else None
        language = guess_track_language(str(raw_track["name"]))
        images = album.get("images") or []
        image_url = str(images[0].get("url")) if images and images[0].get("url") else None
        external_urls = raw_track.get("external_urls") or {}
        external_url = str(external_urls.get("spotify")) if external_urls.get("spotify") else None
        return Track(
            id=str(raw_track["id"]),
            title=str(raw_track["name"]),
            artist_id=str(artist.get("id") or artist.get("name") or "unknown"),
            artist_name=str(artist.get("name") or "Unknown artist"),
            provider=Provider.SPOTIFY,
            provider_uri=raw_track.get("uri"),
            image_url=image_url,
            external_url=external_url,
            album_name=str(album.get("name")) if album.get("name") else None,
            isrc=external_ids.get("isrc"),
            genres=genres,
            release_year=release_year,
            popularity=popularity,
            explicit=bool(raw_track.get("explicit")) if raw_track.get("explicit") is not None else None,
            language=language.language,
            language_confidence=language.confidence,
        )

    @classmethod
    def _listen_from_item(cls, item: dict[str, Any]) -> Listen:
        return Listen(
            track=cls.track_from_raw(item["track"]),
            played_at=datetime.fromisoformat(item["played_at"].replace("Z", "+00:00")),
        )
