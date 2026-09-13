from fastapi.testclient import TestClient
from unloop.api.app import app

client = TestClient(app)


def test_home_embeds_no_doomscroll_product_language() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "No swiping" in response.text
    assert "No doomscrolling" in response.text
    assert "leave blank for default" in response.text


def test_streaming_service_registry_is_provider_agnostic() -> None:
    response = client.get("/v1/streaming-services")
    assert response.status_code == 200
    services = {item["id"]: item for item in response.json()}
    assert services["spotify"]["available"] is True
    assert services["apple_music"]["status"] == "planned"
    assert services["navidrome"]["status"] == "planned"
    assert services["local"]["status"] == "planned"


def test_home_shows_spotify_connection_status_ui() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert 'id="spotifyBadge"' in response.text
    assert "Spotify connected" in response.text
    assert "loadServices" in response.text
