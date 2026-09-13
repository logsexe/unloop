from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field


class Provider(StrEnum):
    SPOTIFY = "spotify"
    LISTENBRAINZ = "listenbrainz"
    MUSICBRAINZ = "musicbrainz"
    LOCAL = "local"




class StreamingService(StrEnum):
    SPOTIFY = "spotify"
    APPLE_MUSIC = "apple_music"
    NAVIDROME = "navidrome"
    LOCAL = "local"


class StreamingServiceStatus(BaseModel):
    id: StreamingService
    name: str
    available: bool
    connected: bool = False
    status: str
    capabilities: tuple[str, ...] = ()


class DiscoveryMode(StrEnum):
    SAFE = "safe"
    EXPLORE = "explore"
    DEEP_CUT = "deep_cut"
    CHAOS = "chaos"
    CUSTOM = "custom"


class LanguagePreference(StrEnum):
    ANY = "any"
    ENGLISH_PREFERRED = "english_preferred"
    ENGLISH_ONLY = "english_only"


class RelatabilityLevel(StrEnum):
    OPEN = "open"
    BALANCED = "balanced"
    CLOSE = "close"


class FeedbackAction(StrEnum):
    LIKE = "like"
    DISLIKE = "dislike"
    SKIP = "skip"
    COOLDOWN = "cooldown"


class RecommendationOutcome(StrEnum):
    UNRATED = "unrated"
    LIKED = "liked"
    DISLIKED = "disliked"
    SKIPPED = "skipped"


class Track(BaseModel):
    id: str
    title: str
    artist_id: str
    artist_name: str
    provider: Provider
    provider_uri: str | None = None
    image_url: str | None = None
    external_url: str | None = None
    album_name: str | None = None
    isrc: str | None = None
    musicbrainz_recording_id: str | None = None
    genres: tuple[str, ...] = ()
    country: str | None = None
    release_year: int | None = Field(default=None, ge=1800, le=2200)
    popularity: float | None = Field(default=None, ge=0, le=1)
    explicit: bool | None = None
    language: str | None = None
    language_confidence: float = Field(default=0.0, ge=0, le=1)


class Listen(BaseModel):
    track: Track
    played_at: datetime


class Candidate(BaseModel):
    track: Track
    taste_similarity: float = Field(default=0.5, ge=0, le=1)
    community_similarity: float = Field(default=0.5, ge=0, le=1)
    source_confidence: float = Field(default=0.5, ge=0, le=1)
    artist_known: bool = False
    artist_saturation: float = Field(default=0.0, ge=0, le=1)
    source: str = "unknown"


class ScoreBreakdown(BaseModel):
    taste_similarity: float
    novelty: float
    artist_unfamiliarity: float
    genre_exploration: float
    community_similarity: float
    serendipity: float
    obscurity: float
    repetition_penalty: float
    final_score: float


class RankedTrack(BaseModel):
    track: Track
    score: ScoreBreakdown
    reasons: tuple[str, ...] = ()
    source: str = "unknown"


class ArtistCooldown(BaseModel):
    artist_id: str
    artist_name: str
    until: datetime
    created_at: datetime


class FeedbackEvent(BaseModel):
    track_id: str
    artist_id: str
    action: FeedbackAction
    created_at: datetime
    cooldown_until: datetime | None = None


class ArtistMetadata(BaseModel):
    provider_artist_id: str
    artist_name: str
    musicbrainz_artist_id: str | None = None
    genres: tuple[str, ...] = ()
    tags: dict[str, int] = Field(default_factory=dict)
    country: str | None = None
    updated_at: datetime


class TasteCluster(BaseModel):
    name: str
    weight: float = Field(ge=0, le=1)
    evidence: tuple[str, ...] = ()


class ArtistSaturation(BaseModel):
    artist_id: str
    artist_name: str
    score: float = Field(ge=0, le=100)
    status: str
    recent_plays: int = 0
    top_track_count: int = 0
    top_artist_rank: int | None = None
    reasons: tuple[str, ...] = ()


class EnrichmentReport(BaseModel):
    requested: int
    cached: int
    enriched: int
    unmatched: int
    failed: int
    failure_reasons: dict[str, int] = Field(default_factory=dict)


class DiscoveryPreferences(BaseModel):
    mode: DiscoveryMode = DiscoveryMode.EXPLORE
    discovery_level: int = Field(default=70, ge=0, le=100)
    max_tracks_per_artist: int = Field(default=1, ge=1, le=10)
    minimum_new_artist_ratio: float = Field(default=0.70, ge=0, le=1)
    popularity_ceiling: float | None = Field(default=None, ge=0, le=1)
    prefer_unheard_tracks: bool = True
    language_preference: LanguagePreference = LanguagePreference.ENGLISH_PREFERRED
    relatability: RelatabilityLevel = RelatabilityLevel.OPEN
    release_year_min: int | None = Field(default=None, ge=1900, le=2200)
    release_year_max: int | None = Field(default=None, ge=1900, le=2200)
    allow_explicit: bool = True
    required_genres: tuple[str, ...] = ()


class RecommendationRecord(BaseModel):
    batch_id: str
    track_id: str
    artist_id: str
    source: str
    final_score: float = Field(ge=0, le=1)
    recommended_at: datetime
    is_new_track: bool = True
    is_new_artist: bool = True
    outcome: RecommendationOutcome = RecommendationOutcome.UNRATED


class BatchAnalytics(BaseModel):
    batch_id: str
    created_at: datetime
    mode: DiscoveryMode
    discovery_level: int = Field(ge=0, le=100)
    track_count: int
    new_track_count: int
    new_artist_count: int
    novelty_rate: float = Field(ge=0, le=1)
    source_breakdown: dict[str, int] = Field(default_factory=dict)
    liked: int = 0
    disliked: int = 0
    skipped: int = 0
    unrated: int = 0
    hit_rate: float | None = Field(default=None, ge=0, le=1)
