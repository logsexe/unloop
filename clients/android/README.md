# UNLOOP Android

Native Android client foundation for UNLOOP.

## Product rule

The mobile app must preserve the core UNLOOP behaviour:

- no swipe-to-discover feed;
- no infinite recommendation stream;
- no streaks or engagement loops;
- finite batches only;
- explicit controls over discovery;
- streaming-service independence.

## Current V0.10 scope

This directory contains the first Jetpack Compose shell for the future mobile client.

Today it provides:

- native UNLOOP visual direction;
- provider-selection surface;
- finite-batch entry point;
- mobile-first information hierarchy;
- Android project structure ready for real API integration.

The buttons are intentionally not wired to Spotify yet. The next mobile milestone is to connect this client to the same provider/discovery boundary used by the Python reference app.

## Toolchain

- Android Gradle Plugin 9.4.0
- Kotlin 2.4.20
- Jetpack Compose BOM 2026.08.00
- minSdk 28
- targetSdk 37
- JDK 17

## Open in Android Studio

Open the `clients/android` directory as a Gradle project.

The project does not yet commit a Gradle wrapper. Android Studio can import the Gradle build directly; a wrapper will be added once the mobile build pipeline is stabilised.

## Near-term mobile roadmap

1. Connections screen
2. Spotify PKCE handoff
3. provider-neutral connection model
4. finite batch builder
5. result cards with artwork and explanations
6. Like / Skip / Nope / Cooldown
7. playlist publishing
8. local secure token storage
9. offline recommendation memory
10. Apple Music adapter
