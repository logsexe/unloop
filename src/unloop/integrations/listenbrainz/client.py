from __future__ import annotations

from typing import Any

import httpx


class ListenBrainzAPI:
    BASE_URL = "https://api.listenbrainz.org/1"

    def __init__(self, token: str = "", client: httpx.AsyncClient | None = None) -> None:
        self.token = token
        self._client = client

    async def _get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Token {self.token}"
        url = f"{self.BASE_URL}{path}"
        if self._client:
            response = await self._client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return dict(response.json()) if response.content else {}
        async with httpx.AsyncClient(timeout=25) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return dict(response.json()) if response.content else {}

    async def recommendations(self, username: str, count: int = 100) -> list[dict[str, Any]]:
        payload = await self._get(
            f"/cf/recommendation/user/{username}/recording",
            {"count": min(max(count, 1), 100), "offset": 0},
        )
        inner = payload.get("payload") or {}
        return list(inner.get("mbids") or [])

    async def recording_metadata(self, mbids: list[str]) -> dict[str, dict[str, Any]]:
        if not mbids:
            return {}
        payload = await self._get(
            "/metadata/recording/",
            {"recording_mbids": ",".join(mbids[:50]), "inc": "artist tag release"},
        )
        return {str(k): dict(v) for k, v in payload.items() if isinstance(v, dict)}
