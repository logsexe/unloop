from fastapi.testclient import TestClient

from unloop.api.app import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_homepage_exists() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "UNLOOP" in response.text


def test_discover_requires_spotify_connection() -> None:
    response = client.get("/v1/discover?discovery_level=90&limit=2")
    assert response.status_code == 409
    assert "Spotify is not connected" in response.json()["detail"]
