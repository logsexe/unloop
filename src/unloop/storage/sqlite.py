from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterator

from unloop.domain.models import (
    ArtistCooldown,
    ArtistMetadata,
    DiscoveryPreferences,
    FeedbackAction,
    FeedbackEvent,
    RecommendationOutcome,
    RecommendationRecord,
    BatchAnalytics,
    DiscoveryMode,
)


class SQLiteStore:
    """Small local-first persistence layer using only Python's stdlib sqlite3."""

    def __init__(self, path: str | Path = "data/unloop.db") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._migrate()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _migrate(self) -> None:
        with self._connect() as db:
            db.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS feedback_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    track_id TEXT NOT NULL,
                    artist_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    cooldown_until TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_feedback_track ON feedback_events(track_id);
                CREATE INDEX IF NOT EXISTS idx_feedback_artist ON feedback_events(artist_id);

                CREATE TABLE IF NOT EXISTS artist_cooldowns (
                    artist_id TEXT PRIMARY KEY,
                    artist_name TEXT NOT NULL,
                    until TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS settings (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS artist_metadata (
                    provider_artist_id TEXT PRIMARY KEY,
                    artist_name TEXT NOT NULL,
                    musicbrainz_artist_id TEXT,
                    genres_json TEXT NOT NULL,
                    tags_json TEXT NOT NULL,
                    country TEXT,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_artist_metadata_mbid
                    ON artist_metadata(musicbrainz_artist_id);

                CREATE TABLE IF NOT EXISTS recommendation_batches (
                    batch_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    discovery_level INTEGER NOT NULL
                );

                CREATE TABLE IF NOT EXISTS recommendation_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    batch_id TEXT NOT NULL,
                    track_id TEXT NOT NULL,
                    artist_id TEXT NOT NULL,
                    source TEXT NOT NULL,
                    final_score REAL NOT NULL,
                    recommended_at TEXT NOT NULL,
                    is_new_track INTEGER NOT NULL DEFAULT 1,
                    is_new_artist INTEGER NOT NULL DEFAULT 1,
                    outcome TEXT NOT NULL DEFAULT 'unrated'
                );
                CREATE INDEX IF NOT EXISTS idx_recommendation_track
                    ON recommendation_history(track_id);
                CREATE INDEX IF NOT EXISTS idx_recommendation_batch
                    ON recommendation_history(batch_id);
                """
            )

    def record_feedback(self, event: FeedbackEvent) -> None:
        with self._connect() as db:
            db.execute(
                """INSERT INTO feedback_events
                (track_id, artist_id, action, created_at, cooldown_until)
                VALUES (?, ?, ?, ?, ?)""",
                (
                    event.track_id,
                    event.artist_id,
                    event.action.value,
                    event.created_at.isoformat(),
                    event.cooldown_until.isoformat() if event.cooldown_until else None,
                ),
            )

    def recent_feedback(self, limit: int = 100) -> list[FeedbackEvent]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM feedback_events ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [
            FeedbackEvent(
                track_id=row["track_id"],
                artist_id=row["artist_id"],
                action=FeedbackAction(row["action"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                cooldown_until=(
                    datetime.fromisoformat(row["cooldown_until"])
                    if row["cooldown_until"]
                    else None
                ),
            )
            for row in rows
        ]

    def set_artist_cooldown(self, cooldown: ArtistCooldown) -> None:
        with self._connect() as db:
            db.execute(
                """INSERT INTO artist_cooldowns (artist_id, artist_name, until, created_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(artist_id) DO UPDATE SET
                    artist_name=excluded.artist_name,
                    until=excluded.until,
                    created_at=excluded.created_at""",
                (
                    cooldown.artist_id,
                    cooldown.artist_name,
                    cooldown.until.isoformat(),
                    cooldown.created_at.isoformat(),
                ),
            )

    def remove_artist_cooldown(self, artist_id: str) -> None:
        with self._connect() as db:
            db.execute("DELETE FROM artist_cooldowns WHERE artist_id = ?", (artist_id,))

    def active_cooldowns(self, now: datetime | None = None) -> list[ArtistCooldown]:
        now = now or datetime.now(UTC)
        with self._connect() as db:
            db.execute("DELETE FROM artist_cooldowns WHERE until <= ?", (now.isoformat(),))
            rows = db.execute("SELECT * FROM artist_cooldowns ORDER BY until").fetchall()
        return [
            ArtistCooldown(
                artist_id=row["artist_id"],
                artist_name=row["artist_name"],
                until=datetime.fromisoformat(row["until"]),
                created_at=datetime.fromisoformat(row["created_at"]),
            )
            for row in rows
        ]

    def save_preferences(self, preferences: DiscoveryPreferences) -> None:
        with self._connect() as db:
            db.execute(
                """INSERT INTO settings(key, value) VALUES('discovery_preferences', ?)
                ON CONFLICT(key) DO UPDATE SET value=excluded.value""",
                (preferences.model_dump_json(),),
            )

    def load_preferences(self) -> DiscoveryPreferences:
        with self._connect() as db:
            row = db.execute(
                "SELECT value FROM settings WHERE key='discovery_preferences'"
            ).fetchone()
        if row is None:
            return DiscoveryPreferences()
        return DiscoveryPreferences.model_validate(json.loads(row["value"]))



    def record_recommendation_batch(
        self,
        batch_id: str,
        created_at: datetime,
        mode: DiscoveryMode,
        discovery_level: int,
        records: list[RecommendationRecord],
    ) -> None:
        with self._connect() as db:
            db.execute(
                """INSERT OR REPLACE INTO recommendation_batches
                (batch_id, created_at, mode, discovery_level) VALUES (?, ?, ?, ?)""",
                (batch_id, created_at.isoformat(), mode.value, discovery_level),
            )
            db.executemany(
                """INSERT INTO recommendation_history
                (batch_id, track_id, artist_id, source, final_score, recommended_at, is_new_track, is_new_artist, outcome)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                [
                    (r.batch_id, r.track_id, r.artist_id, r.source, r.final_score,
                     r.recommended_at.isoformat(), int(r.is_new_track), int(r.is_new_artist), r.outcome.value)
                    for r in records
                ],
            )

    def recommended_track_ids(self, limit: int = 2000) -> set[str]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT track_id FROM recommendation_history ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return {str(row["track_id"]) for row in rows}

    def apply_feedback_to_recommendations(self, event: FeedbackEvent) -> None:
        mapping = {
            FeedbackAction.LIKE: RecommendationOutcome.LIKED,
            FeedbackAction.DISLIKE: RecommendationOutcome.DISLIKED,
            FeedbackAction.SKIP: RecommendationOutcome.SKIPPED,
        }
        outcome = mapping.get(event.action)
        if outcome is None:
            return
        with self._connect() as db:
            db.execute(
                """UPDATE recommendation_history SET outcome = ?
                WHERE id = (SELECT id FROM recommendation_history
                            WHERE track_id = ? ORDER BY id DESC LIMIT 1)""",
                (outcome.value, event.track_id),
            )

    def feedback_bias(self) -> tuple[set[str], set[str], set[str]]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT track_id, artist_id, action FROM feedback_events ORDER BY id DESC LIMIT 1000"
            ).fetchall()
        liked_artists: set[str] = set()
        disliked_artists: set[str] = set()
        rejected_tracks: set[str] = set()
        for row in rows:
            action = str(row["action"])
            if action == FeedbackAction.LIKE.value:
                liked_artists.add(str(row["artist_id"]))
            elif action == FeedbackAction.DISLIKE.value:
                disliked_artists.add(str(row["artist_id"]))
                rejected_tracks.add(str(row["track_id"]))
            elif action == FeedbackAction.SKIP.value:
                rejected_tracks.add(str(row["track_id"]))
        return liked_artists, disliked_artists, rejected_tracks

    def batch_analytics(self, limit: int = 20) -> list[BatchAnalytics]:
        with self._connect() as db:
            batches = db.execute(
                "SELECT * FROM recommendation_batches ORDER BY created_at DESC LIMIT ?", (limit,)
            ).fetchall()
            output: list[BatchAnalytics] = []
            for batch in batches:
                rows = db.execute(
                    "SELECT * FROM recommendation_history WHERE batch_id = ?",
                    (batch["batch_id"],),
                ).fetchall()
                sources: dict[str, int] = {}
                outcomes = {item.value: 0 for item in RecommendationOutcome}
                for row in rows:
                    source = str(row["source"])
                    sources[source] = sources.get(source, 0) + 1
                    outcomes[str(row["outcome"])] = outcomes.get(str(row["outcome"]), 0) + 1
                rated = outcomes[RecommendationOutcome.LIKED.value] + outcomes[RecommendationOutcome.DISLIKED.value] + outcomes[RecommendationOutcome.SKIPPED.value]
                hit = (outcomes[RecommendationOutcome.LIKED.value] / rated) if rated else None
                output.append(BatchAnalytics(
                    batch_id=str(batch["batch_id"]),
                    created_at=datetime.fromisoformat(batch["created_at"]),
                    mode=DiscoveryMode(str(batch["mode"])),
                    discovery_level=int(batch["discovery_level"]),
                    track_count=len(rows),
                    new_track_count=sum(int(row["is_new_track"]) for row in rows),
                    new_artist_count=len({str(row["artist_id"]) for row in rows if int(row["is_new_artist"])}),
                    novelty_rate=(sum(int(row["is_new_track"]) for row in rows) / len(rows)) if rows else 0.0,
                    source_breakdown=sources,
                    liked=outcomes[RecommendationOutcome.LIKED.value],
                    disliked=outcomes[RecommendationOutcome.DISLIKED.value],
                    skipped=outcomes[RecommendationOutcome.SKIPPED.value],
                    unrated=outcomes[RecommendationOutcome.UNRATED.value],
                    hit_rate=hit,
                ))
        return output

    def save_artist_metadata(self, metadata: ArtistMetadata) -> None:
        with self._connect() as db:
            db.execute(
                """INSERT INTO artist_metadata
                (provider_artist_id, artist_name, musicbrainz_artist_id, genres_json,
                 tags_json, country, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(provider_artist_id) DO UPDATE SET
                    artist_name=excluded.artist_name,
                    musicbrainz_artist_id=excluded.musicbrainz_artist_id,
                    genres_json=excluded.genres_json,
                    tags_json=excluded.tags_json,
                    country=excluded.country,
                    updated_at=excluded.updated_at""",
                (
                    metadata.provider_artist_id,
                    metadata.artist_name,
                    metadata.musicbrainz_artist_id,
                    json.dumps(list(metadata.genres)),
                    json.dumps(metadata.tags),
                    metadata.country,
                    metadata.updated_at.isoformat(),
                ),
            )

    def get_artist_metadata(self, provider_artist_id: str) -> ArtistMetadata | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT * FROM artist_metadata WHERE provider_artist_id = ?",
                (provider_artist_id,),
            ).fetchone()
        return self._artist_metadata_from_row(row) if row else None

    def artist_metadata_many(self, provider_artist_ids: list[str]) -> list[ArtistMetadata]:
        if not provider_artist_ids:
            return []
        placeholders = ",".join("?" for _ in provider_artist_ids)
        with self._connect() as db:
            rows = db.execute(
                f"SELECT * FROM artist_metadata WHERE provider_artist_id IN ({placeholders})",
                provider_artist_ids,
            ).fetchall()
        by_id = {row["provider_artist_id"]: self._artist_metadata_from_row(row) for row in rows}
        return [by_id[item] for item in provider_artist_ids if item in by_id]

    def all_artist_metadata(self) -> list[ArtistMetadata]:
        with self._connect() as db:
            rows = db.execute("SELECT * FROM artist_metadata ORDER BY updated_at DESC").fetchall()
        return [self._artist_metadata_from_row(row) for row in rows]

    @staticmethod
    def _artist_metadata_from_row(row: sqlite3.Row) -> ArtistMetadata:
        return ArtistMetadata(
            provider_artist_id=row["provider_artist_id"],
            artist_name=row["artist_name"],
            musicbrainz_artist_id=row["musicbrainz_artist_id"],
            genres=tuple(json.loads(row["genres_json"])),
            tags={str(k): int(v) for k, v in json.loads(row["tags_json"]).items()},
            country=row["country"],
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
