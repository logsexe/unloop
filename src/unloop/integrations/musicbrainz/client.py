from __future__ import annotations

import asyncio
import time
from typing import Any

import httpx


class MusicBrainzAPI:
    """Respectful MusicBrainz client with rate limiting and transient retries."""

    BASE_URL = "https://musicbrainz.org/ws/2"

    def __init__(
        self,
        *,
        user_agent: str,
        client: httpx.AsyncClient | None = None,
        minimum_interval_seconds: float = 1.10,
        max_attempts: int = 3,
    ) -> None:
        self.user_agent = user_agent
        self._client = client
        self._minimum_interval_seconds = minimum_interval_seconds
        self._last_request_monotonic = 0.0
        self._rate_lock = asyncio.Lock()
        self._max_attempts = max_attempts

    async def _wait_for_rate_limit(self) -> None:
        async with self._rate_lock:
            elapsed = time.monotonic() - self._last_request_monotonic
            if elapsed < self._minimum_interval_seconds:
                await asyncio.sleep(self._minimum_interval_seconds - elapsed)
            self._last_request_monotonic = time.monotonic()

    async def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        headers = {"User-Agent": self.user_agent, "Accept": "application/json"}
        url = f"{self.BASE_URL}{path}"
        merged_params = {"fmt": "json", **params}
        last_error: Exception | None = None
        for attempt in range(self._max_attempts):
            await self._wait_for_rate_limit()
            try:
                if self._client:
                    response = await self._client.get(url, headers=headers, params=merged_params)
                else:
                    async with httpx.AsyncClient(timeout=25) as client:
                        response = await client.get(url, headers=headers, params=merged_params)
                if response.status_code in {429, 502, 503, 504}:
                    raise httpx.HTTPStatusError(
                        f"Transient MusicBrainz HTTP {response.status_code}",
                        request=response.request,
                        response=response,
                    )
                response.raise_for_status()
                return dict(response.json())
            except (httpx.TimeoutException, httpx.NetworkError, httpx.HTTPStatusError) as exc:
                last_error = exc
                if attempt + 1 >= self._max_attempts:
                    raise
                await asyncio.sleep(1.5 * (2**attempt))
        if last_error:
            raise last_error
        return {}

    async def search_artist(self, name: str) -> dict[str, Any] | None:
        escaped = name.replace('"', '\\"')
        payload = await self._get("/artist/", {"query": f'artist:"{escaped}"', "limit": 5})
        artists = list(payload.get("artists") or [])
        if not artists:
            return None
        normalized = name.casefold().strip()
        exact = [a for a in artists if str(a.get("name") or "").casefold().strip() == normalized]
        pool = exact or artists
        best = max(pool, key=lambda item: int(item.get("score") or 0))
        if int(best.get("score") or 0) < 85:
            return None
        return await self.artist(str(best["id"]))

    async def artist(self, mbid: str) -> dict[str, Any]:
        return await self._get(f"/artist/{mbid}", {"inc": "genres+tags"})
