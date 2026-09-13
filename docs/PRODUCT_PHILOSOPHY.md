# UNLOOP Product Philosophy

> **Get back your time. Renew your taste.**

UNLOOP is an open-source, streaming-service-agnostic discovery layer. Streaming services play music; UNLOOP decides what deserves to be discovered next.

## The constitutional rules

- **No infinite scroll.** Discovery always ends.
- **No swipe-to-discover feeds.** Music is not a slot machine.
- **No doomscrolling mechanics.** No streaks, FOMO, autoplay queues, engagement nags, or “one more” loops.
- **No ads, sponsored recommendations, paid placement, or pay-to-rank.**
- **No engagement optimisation.** Time in UNLOOP is not a success metric.
- **Finite batches by default.** Ask for music, receive a bounded collection, then leave and listen.
- **Streaming-service agnostic.** Spotify is the first adapter, not the architecture.
- **Explainable discovery.** Users should be able to understand why a track was selected.
- **Portable taste.** Feedback, cooldowns, recommendation memory, and taste signals belong to the user.
- **Local-first where practical.** Preference and recommendation-history data should stay on the user's device unless they intentionally connect an external service.

## Product test

A good UNLOOP session is short:

1. Choose a discovery mode.
2. Request a finite batch.
3. Save or name the playlist.
4. Leave UNLOOP.
5. Listen to music.

**Find music. Save the playlist. Leave.**
