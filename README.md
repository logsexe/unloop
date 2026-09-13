# UNLOOP

> **Get back your time. Renew your taste.**

**UNLOOP is an open-source, streaming-service-agnostic music discovery layer.**

Streaming services play your music. UNLOOP decides what you discover next.

There is **no swipe feed, no infinite scroll, no advertising, no sponsored ranking and no engagement-maximising loop**. Ask for a finite batch, save the playlist, then leave and listen.

> Status: early alpha. Current development build: `0.9.0-dev`.

## V0.9 — Product UI

V0.9 turns the local interface into the beginning of the mobile product: finite discovery, artwork, feedback, taste mapping and analytics.

- polished local app at `http://127.0.0.1:8787/`;
- Spotify as the first working streaming adapter;
- Apple Music, Navidrome and Local Library represented as provider slots from day one;
- finite discovery batches only;
- custom playlist naming or the default `UNLOOP Discovery`;
- provider registry at `GET /v1/streaming-services`;
- recommendation-memory persistence fix;
- product manifesto hardened around **NO SWIPING & NO DOOMSCROLLING**.

Read [V0.9](docs/V09.md) and the [Product Philosophy](docs/PRODUCT_PHILOSOPHY.md).

## Product promise

```text
Choose your streaming service
        ↓
Choose Safe / Explore / Deep Cut / Chaos
        ↓
Request a finite batch
        ↓
Name the playlist (optional)
        ↓
Save it
        ↓
LEAVE UNLOOP AND LISTEN
```

UNLOOP considers a short session a success.

## Streaming-service architecture

UNLOOP separates three concerns:

```text
STREAMING PROVIDERS        DISCOVERY SOURCES       METADATA
Spotify                    ListenBrainz            MusicBrainz
Apple Music (planned)      future open sources
Navidrome (planned)
Local Library (planned)
          \                    |                    /
           \                   |                   /
                    UNLOOP CORE
          novelty · saturation · diversity
          memory · feedback · explainability
                         |
                  finite playlist
```

Spotify is the first adapter, not the architecture.

## Current capabilities

- Spotify OAuth PKCE and listening-history import;
- optional ListenBrainz collaborative candidates;
- MusicBrainz enrichment with local caching;
- Safe / Explore / Deep Cut / Chaos modes;
- novelty and artist-unfamiliarity ranking;
- artist saturation and cooldowns;
- recommendation memory;
- explicit like / skip / dislike feedback;
- local SQLite persistence;
- batch analytics and hit-rate tracking;
- custom playlist names;
- finite private Spotify playlist publishing;
- provider-independent discovery core.

## Quick start

Requires Python 3.12+.

```bash
git clone https://github.com/logsexe/unloop.git
cd unloop
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
cp .env.example .env
uvicorn unloop.api.app:app --reload --port 8787
```

Windows PowerShell activation:

```powershell
.\.venv\Scripts\Activate.ps1
```

Open:

```text
http://127.0.0.1:8787/
```

The UI can connect Spotify, choose a discovery mode, select a finite batch size and optionally name the playlist.

## Spotify development setup

Create an app in the Spotify Developer Dashboard and configure this redirect URI exactly:

```text
http://127.0.0.1:8787/v1/connections/spotify/callback
```

Then add the client ID to `.env`:

```text
UNLOOP_SPOTIFY_CLIENT_ID=your_client_id
```

UNLOOP uses PKCE; do not put a Spotify client secret in the mobile app or public repository.

## Playlist naming

Leave the playlist-name field blank to use:

```text
UNLOOP Discovery
```

Or enter any name up to 100 characters, for example:

```text
Saturday Night Deep Cuts
Long Run 01
Electronic Reset
Things Spotify Forgot
```

The API equivalent is:

```text
POST /v1/playlists/discovery?mode=explore&limit=30&playlist_name=Electronic%20Reset
```

## Philosophy

UNLOOP will not ship:

- infinite discovery feeds;
- swipe-to-discover mechanics;
- streaks or FOMO loops;
- sponsored recommendations;
- paid ranking;
- advertisements;
- time-on-platform optimisation.

The core product test is simple:

> **Find music. Save the playlist. Leave.**

## Development

```bash
pytest
ruff check .
mypy src/unloop
```

## License

MIT.


## Guided discovery filters (V0.9)

UNLOOP now supports language preference, relatability, release-year bounds, explicit-content filtering, and optional genre/scene constraints. `English only` is explicitly best-effort because Spotify does not expose canonical track-language metadata; UNLOOP refuses to fake certainty and uses conservative language signals instead.
