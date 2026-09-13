# ListenBrainz integration

V0.5 can mix ListenBrainz collaborative-filtering recording recommendations into the UNLOOP candidate pool.

1. Create a free ListenBrainz / MetaBrainz account.
2. Add listening data to ListenBrainz; the service can automatically submit Spotify listens after you connect Spotify on ListenBrainz.
3. Put your ListenBrainz username in `.env`:

   `UNLOOP_LISTENBRAINZ_USERNAME=your_username`

4. Restart UNLOOP and check `/v1/connections/listenbrainz`.
5. Generate `/v1/discover?mode=explore&limit=30`.

Tracks sourced from collaborative filtering include `source: "listenbrainz-cf"` and the explanation `ListenBrainz collaborative recommendation`.

The integration degrades gracefully: if ListenBrainz has no recommendations yet or is unavailable, Spotify catalogue discovery still builds the batch.
