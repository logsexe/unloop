## 0.9.0-dev

- Product-facing Discover / Taste / Analytics interface.
- Album artwork and direct streaming-service track links.
- Like, Skip, Nope, and 90-day cooldown controls in the UI.
- Taste cluster and artist saturation views.
- Batch novelty / hit-rate analytics.
- GitHub-first project workflow.

# Development changelog

## 0.4.0-dev

- Added MusicBrainz artist metadata enrichment and a local SQLite metadata cache.
- Added a rate-limited MusicBrainz client that identifies UNLOOP with a configurable contact URL/email.
- Added `POST /v1/enrichment/musicbrainz` and `GET /v1/enrichment/status`.
- Added open genre/tag enrichment for Spotify artists whose genre arrays are empty.
- Added transparent taste clustering across broad parent scenes.
- Added artist saturation scores combining recent plays, top-track concentration and top-artist rank.
- Fixed long-term familiar artists being mistaken for new artists when absent from recent history.
- Added saturation-aware ranking penalties without automatically blocking liked artists.
- Expanded `/v1/taste` with `taste_clusters`, `artist_saturation` and metadata coverage.
- Added tests for clustering, metadata persistence, long-term familiarity and saturation.

### Known limitations

- MusicBrainz artist matching is name-based and intentionally conservative; ambiguous artists can remain unmatched.
- The first metadata sync is deliberately slow because UNLOOP respects MusicBrainz's public one-request-per-second policy.
- Spotify OAuth tokens remain memory-only across process restarts.
- Candidate generation is still Spotify-search-first; ListenBrainz collaborative recommendations are planned for 0.5.
- Taste clustering is a transparent heuristic taxonomy, not an ML model.
