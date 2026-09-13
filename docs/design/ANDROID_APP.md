# Android companion app design

## Product role

The Android app is a companion discovery client. Spotify remains responsible for licensed playback. UNLOOP decides what deserves to be discovered.

The app should work well on privacy-focused Android distributions and must not require Firebase, Google Analytics, Google Sign-In or Google Play Services for core operation.

## Navigation

Use four primary destinations only:

1. **Discover** — finite recommendation batch.
2. **Library** — saved UNLOOP discoveries and feedback history.
3. **Taste** — transparent taste graph and exploration controls.
4. **Settings** — providers, privacy, export and advanced controls.

Do not add a social feed or engagement tab.

## Discover screen

The default screen shows one finite batch, e.g. 20–30 tracks.

Each card exposes:

- artwork;
- title and artist;
- UNLOOP score;
- 2–3 concise reasons;
- Play in Spotify;
- Like;
- Not for me;
- Cooldown artist.

At the end of the batch show a deliberate action such as **Generate another batch**, never automatic pagination.

## Discovery control

A single prominent 0–100 dial is supported, with presets:

- Safe
- Explore
- Deep Cut
- Chaos

Advanced settings may expose minimum-new-artist ratio, popularity ceiling and artist repetition limits.

## Spotify handoff

Preferred implementation:

- OAuth Authorization Code + PKCE for account access;
- Spotify App Remote SDK when available for seamless playback control;
- fallback to Spotify deep links/URIs;
- no Spotify password ever enters UNLOOP.

## Local security

On Android:

- OAuth refresh tokens belong in Android Keystore-backed encrypted storage;
- preferences/taste data live in a local Room/SQLite database;
- exported backups are opt-in;
- telemetry defaults to off; reference builds should contain no third-party analytics SDK.

## Visual direction

Dark, restrained and utilitarian rather than a Spotify clone.

- near-black surfaces;
- strong typography;
- album artwork provides most of the colour;
- one accent colour at most;
- generous spacing;
- no autoplay video;
- no animated attention traps;
- no badges or streaks.

The interface should feel like a **music exploration instrument**, not a content feed.
