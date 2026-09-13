# UNLOOP

> **Get back your time. Renew your taste.**

UNLOOP is an open-source, streaming-service-agnostic music discovery layer.

Streaming services play your music. **UNLOOP decides what you discover next.**

No swiping. No infinite feed. No ads. No sponsored ranking. No engagement loop.

**Find music. Save the playlist. Leave.**

## V1 Developer Preview

V1 is the first end-to-end UNLOOP milestone: the discovery engine and native Android client now work together.

From Android you can:

- connect to an UNLOOP engine on your local network;
- see whether Spotify is connected;
- start Spotify OAuth;
- choose Safe / Explore / Deep Cut / Chaos;
- choose 15 / 30 / 45 tracks;
- prefer English, require English best-effort, or allow any language;
- control relatability;
- seed a genre / scene;
- name the playlist or keep the default;
- create a finite playlist and open it in your streaming app.

The Android client deliberately ends after the batch is created. There is no next-feed queue.

## Why

Music discovery should not become another feed to scroll.

UNLOOP gives you a finite batch selected for relevance, novelty and exploration. It remembers what it already recommended, avoids overexposed artists, lets you control how adventurous discovery should be, and explains the ranking rather than hiding behind a black box.

The goal is simple: **spend less time choosing music and more time listening to it.**

## What works

- Spotify OAuth PKCE and listening-history import
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
- direct private Spotify playlist publishing
- native Android client under `clients/android`

Spotify is the first streaming adapter, **not the architecture**. Apple Music, Navidrome and local libraries remain provider targets.

## Principles

UNLOOP will not ship:

- infinite discovery feeds
- swipe-to-discover mechanics
- streaks or FOMO loops
- sponsored recommendations
- paid ranking
- advertising
- time-on-platform optimisation

UNLOOP is built around finite discovery, explicit control, explainable ranking, local-first data, portable taste and provider independence.

## Run the engine

Requires Python 3.12+.

```bash
git clone https://github.com/logsexe/unloop.git
cd unloop
git checkout release/v1
python -m venv .venv
```

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
Copy-Item .env.example .env
uvicorn unloop.api.app:app --host 0.0.0.0 --reload --port 8787
```

Set `UNLOOP_SPOTIFY_CLIENT_ID` in `.env` and configure this redirect URI in your Spotify developer app:

```text
http://127.0.0.1:8787/v1/connections/spotify/callback
```

For desktop use, open `http://127.0.0.1:8787/`.

## Android

Open `clients/android` in Android Studio.

The emulator defaults to:

```text
http://10.0.2.2:8787
```

On a physical phone, enter the LAN address of the computer running UNLOOP, for example:

```text
http://192.168.1.50:8787
```

The current Android preview allows cleartext HTTP only to make local-network development simple. A production distribution must move remote traffic to HTTPS and persistent credentials to platform-secure storage.

## V1 boundary

V1 Developer Preview is intended for self-hosted/local testing. It is **not yet** a Play Store or App Store production release.

Before public-store distribution we still need persistent secure mobile auth, hardened networking, full native feedback/result detail, accessibility review, Apple Music implementation, and release signing.

See [`docs/V1.md`](docs/V1.md) for the milestone contract.

## Development

```bash
pytest
ruff check .
mypy src/unloop
```

## License

MIT.
