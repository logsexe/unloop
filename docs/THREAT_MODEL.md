# Threat model

UNLOOP handles listening history, taste preferences and provider credentials. Treat all three as private user data.

## Assets

- Spotify OAuth access/refresh tokens;
- listening history;
- explicit likes/dislikes;
- artist cooldowns;
- taste profile;
- provider identifiers.

## Primary risks

### Token theft

A stolen refresh token could allow API access within granted scopes. Mobile production builds must store provider tokens using OS-backed secure storage. Tokens must never be logged or committed.

### Over-broad scopes

Request only scopes used by active features. Document every requested scope and why it exists.

### Local database disclosure

The database can reveal listening behaviour. Mobile builds should use application-private storage and support deliberate export rather than world-readable files.

### Malicious recommendation source

Candidate providers are untrusted inputs. Validate all remote payloads and keep ranking logic independent of provider-supplied sponsored metadata.

### Dependency/supply-chain compromise

Keep the dependency footprint small, pin/scan release dependencies and use automated dependency review for pull requests.

## Telemetry

Reference builds should not transmit analytics or crash reports to third parties by default. Diagnostics should be opt-in and clearly documented.
