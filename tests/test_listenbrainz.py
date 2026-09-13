from __future__ import annotations

import httpx
import pytest

from unloop.integrations.listenbrainz import ListenBrainzAPI


@pytest.mark.asyncio
async def test_listenbrainz_recommendations_and_metadata() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if "/cf/recommendation/" in str(request.url):
            return httpx.Response(
                200,
                json={"payload": {"mbids": [{"recording_mbid": "abc", "score": 9.2}]}},
            )
        return httpx.Response(
            200,
            json={"abc": {"recording_name": "Signal", "artist_credit_name": "New Artist"}},
        )

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        api = ListenBrainzAPI(client=client)
        recs = await api.recommendations("tester", 10)
        metadata = await api.recording_metadata(["abc"])

    assert recs[0]["recording_mbid"] == "abc"
    assert metadata["abc"]["recording_name"] == "Signal"
