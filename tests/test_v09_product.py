from fastapi.testclient import TestClient

from unloop.api.app import app
from unloop.integrations.spotify.client import SpotifyAPI


def test_home_has_no_swipe_and_product_tabs() -> None:
    html = TestClient(app).get('/').text
    assert 'No swiping' in html
    assert 'No doomscrolling' in html
    assert 'Taste' in html
    assert 'Analytics' in html
    assert 'Cool 90d' in html
    assert 'Create discovery playlist' in html
    assert 'English preferred' in html
    assert 'Stay close to my taste' in html
    assert 'leave blank for default' in html


def test_health_reports_release_version() -> None:
    response = TestClient(app).get('/health')
    assert response.status_code == 200
    assert response.json()['version'] == '0.9.0'


def test_spotify_track_parses_artwork_and_external_url() -> None:
    track = SpotifyAPI.track_from_raw({
        'id': 't1',
        'name': 'Signal',
        'uri': 'spotify:track:t1',
        'external_urls': {'spotify': 'https://open.spotify.com/track/t1'},
        'artists': [{'id': 'a1', 'name': 'Artist'}],
        'album': {
            'name': 'Album',
            'release_date': '2025-01-01',
            'images': [{'url': 'https://images.example/cover.jpg'}],
        },
        'external_ids': {'isrc': 'ABC123'},
        'explicit': False,
    })
    assert track.image_url == 'https://images.example/cover.jpg'
    assert track.external_url == 'https://open.spotify.com/track/t1'
    assert track.album_name == 'Album'
