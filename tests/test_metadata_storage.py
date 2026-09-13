from datetime import UTC, datetime

from unloop.domain.models import ArtistMetadata
from unloop.storage import SQLiteStore


def test_artist_metadata_round_trip(tmp_path) -> None:
    store = SQLiteStore(tmp_path / "unloop.db")
    item = ArtistMetadata(
        provider_artist_id="spotify-1",
        artist_name="Test Artist",
        musicbrainz_artist_id="mbid-1",
        genres=("house", "electronic"),
        tags={"ambient": 8},
        country="AU",
        updated_at=datetime.now(UTC),
    )
    store.save_artist_metadata(item)
    loaded = store.get_artist_metadata("spotify-1")
    assert loaded is not None
    assert loaded.musicbrainz_artist_id == "mbid-1"
    assert loaded.genres == ("house", "electronic")
    assert loaded.tags["ambient"] == 8
