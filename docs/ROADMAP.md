# Roadmap

UNLOOP uses small vertical releases. A feature is not complete until privacy, failure modes and provider-independence are documented.

## 0.1 — Foundation ✅
- [x] Provider-agnostic domain model
- [x] Explainable novelty-weighted scorer
- [x] Offline mock provider
- [x] FastAPI endpoints
- [x] Docker and CI
- [x] Baseline tests

## 0.2 — Control + connection ✅
- [x] Safe / Explore / Deep Cut / Chaos presets
- [x] New-artist ratio and per-artist caps
- [x] Artist cooldowns + explicit feedback
- [x] SQLite persistence
- [x] Spotify PKCE OAuth
- [x] Spotify recent/top-items primitives

## 0.3 — First live vertical slice ✅
- [x] Real Spotify history provider
- [x] Spotify catalog candidate generation
- [x] Private Spotify playlist publishing
- [x] Token refresh while process is running
- [x] `/v1/taste` inspection endpoint
- [x] Local status screen

## 0.4 — Taste intelligence + open metadata ✅
- [x] MusicBrainz artist identity enrichment
- [x] Respectful one-request-per-second MusicBrainz client
- [x] Local artist metadata cache
- [x] Open genre/tag enrichment
- [x] Multi-cluster taste summary
- [x] Artist saturation model
- [x] Distinguish long-term familiarity from recent repetition
- [x] Saturation-aware recommendation penalty
- [x] Metadata coverage reporting

## 0.5 — Open discovery graph
- [ ] ListenBrainz account connection
- [ ] ListenBrainz collaborative-filtering candidate source
- [ ] Recording MBID mapping and recording-tag enrichment
- [ ] Multi-source candidate deduplication
- [ ] Source-diversity constraints per batch
- [ ] Feedback-aware taste adjustment
- [ ] Track/artist blocklists

## 0.6 — Portable outputs
- [ ] M3U export
- [ ] Taste profile JSON export/import
- [ ] Navidrome/Subsonic-compatible export
- [ ] Provider capability detection
- [ ] Secure persistent desktop token-store abstraction

## 0.7 — Android alpha
- [ ] Kotlin + Jetpack Compose shell
- [ ] Discover / Library / Taste / Settings navigation
- [ ] Finite discovery batches
- [ ] Discovery dial + presets
- [ ] Recommendation explanations
- [ ] Like / dislike / cooldown controls
- [ ] Android Keystore token storage
- [ ] Room local database
- [ ] Spotify App Remote/deep-link handoff
- [ ] No analytics SDKs

## 1.0 — Public release
- [ ] Stable configuration/export schemas
- [ ] Security review
- [ ] Provider setup wizard
- [ ] Accessibility review
- [ ] Documentation site
- [ ] Signed release automation
- [ ] Reproducible Android builds where practical
- [ ] Public contribution/governance policy
