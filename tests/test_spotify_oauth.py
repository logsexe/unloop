from urllib.parse import parse_qs, urlparse

from unloop.integrations.spotify.oauth import create_pkce_request


def test_pkce_request_has_no_client_secret() -> None:
    request = create_pkce_request("client-id", "http://127.0.0.1/callback")
    query = parse_qs(urlparse(request.authorization_url).query)
    assert query["client_id"] == ["client-id"]
    assert query["code_challenge_method"] == ["S256"]
    assert "client_secret" not in query
    assert request.code_verifier
    assert request.state
