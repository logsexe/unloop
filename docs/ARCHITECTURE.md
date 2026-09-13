# Architecture

UNLOOP separates **taste intelligence** from **playback providers**.

```text
 listening sources                      candidate sources
 Spotify / ListenBrainz / local         ListenBrainz / Troi / future
          |                                      |
          v                                      v
   normalized Listen[]                    Candidate[]
          |                                      |
          +------------------+-------------------+
                             v
                    +------------------+
                    | UNLOOP CORE      |
                    | scorer           |
                    | cooldown filter  |
                    | diversity rules  |
                    | explanations     |
                    +--------+---------+
                             |
                             v
                       RankedTrack[]
                             |
                 +-----------+-----------+
                 |                       |
                 v                       v
            Android/UI               outputs
                                  Spotify / M3U /
                                   Navidrome
```

## Architectural rule

No Spotify-specific data structure, policy or SDK type belongs in the recommendation core. Provider adapters normalize external data into UNLOOP domain objects.

## Provider contracts

- `HistoryProvider`: supplies normalized listening history.
- `CandidateProvider`: proposes tracks with upstream similarity/confidence signals.
- `PlaylistProvider`: exports ranked tracks to a destination.

Future contracts will cover playback handoff and identity enrichment.

## Local data

SQLite stores user-owned state such as:

- preferences;
- explicit feedback;
- artist cooldowns;
- eventually normalized history and taste graph data.

Provider OAuth tokens are deliberately **not** stored in this SQLite database by the current development flow. Production Android tokens belong in OS-backed secure storage.

## Ranking philosophy

Current score signals:

| Signal | Default weight |
|---|---:|
| Taste similarity | 27% |
| Track novelty | 24% |
| Artist unfamiliarity | 19% |
| Genre exploration | 10% |
| Community similarity | 8% |
| Obscurity | 7% |
| Serendipity | 5% |

A separate repetition penalty is applied to tracks and artists that dominate recent listening. `discovery_level` changes how aggressively novelty is rewarded and repetition is penalized.

After raw ranking, a diversity pass can enforce:

- minimum proportion of previously unheard artists;
- maximum tracks from one artist;
- popularity ceiling;
- active artist cooldowns.

These are hard user controls rather than hidden engagement heuristics.

## Spotify integration

The planned phone architecture uses OAuth Authorization Code with PKCE. Spotify remains an external provider for account data and playback; UNLOOP never receives a Spotify password.

During development, the FastAPI flow keeps OAuth tokens in memory only. The Android app will use Keystore-backed secure storage.

## Finite discovery

The API returns explicit finite batches. There is no cursor whose purpose is to drive an endless UI feed. Clients may request another batch only through a deliberate user action.

## V0.5 multi-source discovery

UNLOOP treats playback and discovery as separate concerns. Spotify remains a playback/catalogue adapter, while ListenBrainz can contribute independent collaborative-filtering candidates. Candidate sources are merged and deduplicated before transparent UNLOOP scoring. Any external source may fail without taking down the whole batch.

ListenBrainz is optional. Set `UNLOOP_LISTENBRAINZ_USERNAME` to enable collaborative-filtering candidates once that ListenBrainz account has enough listening history for recommendations. `UNLOOP_LISTENBRAINZ_TOKEN` is reserved for future authenticated feedback/sync work and is not required for the public recommendation endpoint.
