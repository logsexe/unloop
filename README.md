# UNLOOP

> **Get back your time. Renew your taste.**

UNLOOP is an open-source, streaming-service-agnostic music discovery layer.

Streaming services play your music. **UNLOOP decides what you discover next.**

No swiping. No infinite feed. No ads. No sponsored ranking. No engagement loop.

**Find music. Save the playlist. Leave.**

## Why

Music discovery should not become another feed to scroll.

UNLOOP gives you a finite batch of music selected for relevance, novelty and exploration. It remembers what it already recommended, avoids overexposed artists, lets you control how adventurous discovery should be, and explains why a track made the cut.

The goal is simple: **spend less time choosing music and more time listening to it.**

## What works today

- Spotify connection via OAuth PKCE
- Spotify listening-history import
- finite discovery batches
- Safe / Explore / Deep Cut / Chaos modes
- custom playlist names
- language, relatability, year, genre and explicit-content filters
- ListenBrainz collaborative candidates
- MusicBrainz metadata enrichment
- artist saturation and cooldowns
- recommendation memory
- Like / Skip / Nope feedback
- local SQLite persistence
- taste and batch analytics
- direct playlist publishing to Spotify

Spotify is the first streaming adapter, **not the architecture**. Apple Music, Navidrome and local libraries are planned providers.

## Principles

UNLOOP will not ship:

- infinite discovery feeds
- swipe-to-discover mechanics
- streaks or FOMO loops
- sponsored recommendations
- paid ranking
- advertising
- time-on-platform optimisation

UNLOOP is built around:

- finite discovery
- explicit user control
- explainable ranking
- local-first data
- portable taste
- streaming-provider independence

## Quick start

Requires Python 3.12+.

```bash
git clone https://github.com/logsexe/unloop.git
cd unloop
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
Copy-Item .env.example .env
uvicorn unloop.api.app:app --reload --port 8787
```

macOS / Linux:

```bash
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
uvicorn unloop.api.app:app --reload --port 8787
```

Open `http://127.0.0.1:8787/`.

For Spotify development, create a Spotify developer app and set the redirect URI to:

```text
http://127.0.0.1:8787/v1/connections/spotify/callback
```

Then add your client ID to `.env`:

```text
UNLOOP_SPOTIFY_CLIENT_ID=your_client_id
```

## Mobile

V0.10 begins the native mobile path. The Python application remains the reference discovery engine while native clients are developed under `clients/`.

- `clients/android` — native Android / Jetpack Compose foundation
- iOS — planned

The mobile goal is the same: **request a finite batch, save it to your streaming service, and leave.**

## Development

```bash
pytest
ruff check .
mypy src/unloop
```

## Status

Early alpha — current release: **V0.9**. The next development line is **V0.10**.

## License

MIT.
