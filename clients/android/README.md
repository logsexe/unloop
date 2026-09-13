# UNLOOP Android

Native Android client for the UNLOOP V1 Developer Preview.

## Product rule

The mobile app must preserve the core UNLOOP behaviour:

- no swipe-to-discover feed;
- no infinite recommendation stream;
- no streaks or engagement loops;
- finite batches only;
- explicit discovery controls;
- streaming-service independence.

## V1 Developer Preview

The Android client now talks to the real UNLOOP engine.

It supports:

- configurable engine URL;
- engine health check;
- Spotify connected/not-connected state;
- Spotify OAuth browser handoff;
- Safe / Explore / Deep Cut / Chaos;
- 15 / 30 / 45-track batches;
- language preference;
- relatability control;
- optional genre/scene seed;
- optional playlist name;
- finite playlist creation;
- open-playlist handoff when the batch is finished.

There is deliberately no next-feed action after completion.

## Toolchain

- Android Gradle Plugin 9.4.0
- Kotlin 2.4.20
- Jetpack Compose BOM 2026.08.00
- minSdk 28
- targetSdk 37
- JDK 17

## Run with the Android emulator

Start the Python engine from the repository root:

```bash
uvicorn unloop.api.app:app --host 0.0.0.0 --reload --port 8787
```

Open `clients/android` in Android Studio and run the app. The default engine address is:

```text
http://10.0.2.2:8787
```

Tap **CHECK CONNECTION**.

## Run on a physical Android phone

The computer and phone must be able to reach each other on the local network.

Run the engine with `--host 0.0.0.0`, then enter the computer's LAN address in the app, for example:

```text
http://192.168.1.50:8787
```

The developer preview permits cleartext HTTP for local-network testing. Do not expose this development server directly to the internet.

## Next hardening milestones

1. secure persistent mobile credentials;
2. native OAuth callback/deep-link handling;
3. richer result cards with artwork and recommendation explanations;
4. Like / Skip / Nope / Cooldown from Android;
5. HTTPS-only remote networking;
6. offline recommendation memory and on-device-core strategy;
7. Apple Music adapter;
8. iOS client.
