from __future__ import annotations

from datetime import UTC, datetime

from unloop.domain.models import ArtistMetadata, EnrichmentReport
from unloop.integrations.musicbrainz import MusicBrainzAPI
from unloop.providers.spotify import SpotifyProvider
from unloop.storage import SQLiteStore


class MetadataEnrichmentService:
    def __init__(
        self,
        spotify: SpotifyProvider,
        musicbrainz: MusicBrainzAPI,
        store: SQLiteStore,
    ) -> None:
        self.spotify = spotify
        self.musicbrainz = musicbrainz
        self.store = store

    async def enrich_top_artists(self, limit: int = 12, force: bool = False) -> EnrichmentReport:
        artists = (await self.spotify.top_artists_raw())[:limit]
        cached = enriched = unmatched = failed = 0
        failure_reasons: dict[str, int] = {}

        for artist in artists:
            provider_id = str(artist.get("id") or "")
            name = str(artist.get("name") or "").strip()
            if not provider_id or not name:
                continue
            existing = self.store.get_artist_metadata(provider_id)
            if existing and not force:
                cached += 1
                continue

            try:
                match = await self.musicbrainz.search_artist(name)
            except Exception as exc:
                failed += 1
                key = type(exc).__name__
                failure_reasons[key] = failure_reasons.get(key, 0) + 1
                continue

            if not match:
                unmatched += 1
                self.store.save_artist_metadata(
                    ArtistMetadata(
                        provider_artist_id=provider_id,
                        artist_name=name,
                        updated_at=datetime.now(UTC),
                    )
                )
                continue

            genres = tuple(
                str(item.get("name"))
                for item in (match.get("genres") or [])
                if item.get("name")
            )
            tags = {
                str(item.get("name")): int(item.get("count") or 1)
                for item in (match.get("tags") or [])
                if item.get("name")
            }
            area = match.get("area") or {}
            country = match.get("country") or area.get("name")
            self.store.save_artist_metadata(
                ArtistMetadata(
                    provider_artist_id=provider_id,
                    artist_name=name,
                    musicbrainz_artist_id=str(match.get("id") or "") or None,
                    genres=genres,
                    tags=tags,
                    country=str(country) if country else None,
                    updated_at=datetime.now(UTC),
                )
            )
            enriched += 1

        return EnrichmentReport(
            requested=len(artists),
            cached=cached,
            enriched=enriched,
            unmatched=unmatched,
            failed=failed,
            failure_reasons=failure_reasons,
        )
