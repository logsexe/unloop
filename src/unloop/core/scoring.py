from __future__ import annotations

import hashlib
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from unloop.domain.models import Candidate, DiscoveryPreferences, LanguagePreference, Listen, RankedTrack, RelatabilityLevel, ScoreBreakdown


@dataclass(frozen=True, slots=True)
class DiscoveryWeights:
    taste_similarity: float = 0.27
    novelty: float = 0.24
    artist_unfamiliarity: float = 0.19
    genre_exploration: float = 0.10
    community_similarity: float = 0.08
    serendipity: float = 0.05
    obscurity: float = 0.07


class DiscoveryScorer:
    """Rank tracks for discovery rather than engagement.

    The scorer has no concept of session length, click-through rate, retention,
    advertising value, sponsored placement, or time-on-platform.
    """

    def __init__(
        self,
        discovery_level: int = 70,
        weights: DiscoveryWeights | None = None,
        preferences: DiscoveryPreferences | None = None,
    ) -> None:
        if not 0 <= discovery_level <= 100:
            raise ValueError("discovery_level must be between 0 and 100")
        self.discovery_level = discovery_level
        self.weights = weights or DiscoveryWeights()
        self.preferences = preferences or DiscoveryPreferences(discovery_level=discovery_level)

    def rank(
        self,
        candidates: list[Candidate],
        history: list[Listen],
        limit: int = 30,
        now: datetime | None = None,
        cooldown_artist_ids: set[str] | None = None,
        previously_recommended_track_ids: set[str] | None = None,
        liked_artist_ids: set[str] | None = None,
        disliked_artist_ids: set[str] | None = None,
        rejected_track_ids: set[str] | None = None,
    ) -> list[RankedTrack]:
        now = now or datetime.now(UTC)
        cooldown_artist_ids = cooldown_artist_ids or set()
        previously_recommended_track_ids = previously_recommended_track_ids or set()
        liked_artist_ids = liked_artist_ids or set()
        disliked_artist_ids = disliked_artist_ids or set()
        rejected_track_ids = rejected_track_ids or set()
        history_window = [item for item in history if item.played_at >= now - timedelta(days=90)]

        track_counts = Counter(item.track.id for item in history_window)
        artist_counts = Counter(item.track.artist_id for item in history_window)
        heard_genres = Counter(genre for item in history_window for genre in item.track.genres)

        eligible = [
            candidate
            for candidate in candidates
            if candidate.track.artist_id not in cooldown_artist_ids
            and candidate.track.id not in previously_recommended_track_ids
            and candidate.track.id not in rejected_track_ids
            and candidate.track.artist_id not in disliked_artist_ids
            and self._within_popularity_ceiling(candidate)
            and self._matches_filters(candidate)
        ]
        ranked = [
            self._score(candidate, track_counts, artist_counts, heard_genres, liked_artist_ids)
            for candidate in eligible
        ]
        ranked.sort(key=lambda item: item.score.final_score, reverse=True)
        return self._diversify(ranked, artist_counts, limit)


    def _matches_filters(self, candidate: Candidate) -> bool:
        track = candidate.track
        prefs = self.preferences
        if not prefs.allow_explicit and track.explicit is True:
            return False
        if prefs.release_year_min is not None and track.release_year is not None and track.release_year < prefs.release_year_min:
            return False
        if prefs.release_year_max is not None and track.release_year is not None and track.release_year > prefs.release_year_max:
            return False
        if prefs.required_genres:
            haystack = {g.casefold() for g in track.genres}
            needles = {g.casefold() for g in prefs.required_genres}
            if not haystack or not any(any(n in h or h in n for h in haystack) for n in needles):
                return False
        if prefs.language_preference is LanguagePreference.ENGLISH_ONLY:
            if track.language == "non_english" and track.language_confidence >= 0.75:
                return False
        taste_floor = {
            RelatabilityLevel.OPEN: 0.0,
            RelatabilityLevel.BALANCED: 0.58,
            RelatabilityLevel.CLOSE: 0.72,
        }[prefs.relatability]
        return candidate.taste_similarity >= taste_floor

    def _within_popularity_ceiling(self, candidate: Candidate) -> bool:
        ceiling = self.preferences.popularity_ceiling
        popularity = candidate.track.popularity
        return ceiling is None or popularity is None or popularity <= ceiling

    def _diversify(
        self,
        ranked: list[RankedTrack],
        artist_counts: Counter[str],
        limit: int,
    ) -> list[RankedTrack]:
        selected: list[RankedTrack] = []
        per_artist: Counter[str] = Counter()
        new_artist_count = 0
        required_new = round(limit * self.preferences.minimum_new_artist_ratio)

        # First pass deliberately satisfies the new-artist floor when possible.
        for item in ranked:
            if len(selected) >= required_new:
                break
            artist_id = item.track.artist_id
            if artist_counts[artist_id] != 0:
                continue
            if per_artist[artist_id] >= self.preferences.max_tracks_per_artist:
                continue
            selected.append(item)
            per_artist[artist_id] += 1
            new_artist_count += 1

        selected_ids = {item.track.id for item in selected}
        for item in ranked:
            if len(selected) >= limit:
                break
            if item.track.id in selected_ids:
                continue
            artist_id = item.track.artist_id
            if per_artist[artist_id] >= self.preferences.max_tracks_per_artist:
                continue
            selected.append(item)
            selected_ids.add(item.track.id)
            per_artist[artist_id] += 1
            if artist_counts[artist_id] == 0:
                new_artist_count += 1

        return selected

    def _score(
        self,
        candidate: Candidate,
        track_counts: Counter[str],
        artist_counts: Counter[str],
        heard_genres: Counter[str],
        liked_artist_ids: set[str],
    ) -> RankedTrack:
        track = candidate.track
        track_plays = track_counts[track.id]
        artist_plays = artist_counts[track.artist_id]

        novelty = 1.0 if track_plays == 0 else max(0.0, 1.0 - (track_plays * 0.45))
        artist_unfamiliarity = max(0.0, 1.0 - min(artist_plays / 12, 1.0))
        if candidate.artist_known:
            artist_unfamiliarity = min(artist_unfamiliarity, 0.20)

        if not track.genres:
            genre_exploration = 0.5
        else:
            unseen = sum(1 for genre in track.genres if heard_genres[genre] == 0)
            genre_exploration = unseen / len(track.genres)

        popularity = track.popularity
        obscurity = 0.5 if popularity is None else 1.0 - popularity

        # Stable pseudo-randomness prevents constantly changing results while still
        # giving similarly scored candidates some serendipity.
        digest = hashlib.sha256(f"{track.artist_id}:{track.id}".encode()).digest()
        serendipity = int.from_bytes(digest[:2], "big") / 65535

        level = self.discovery_level / 100
        novelty_boost = 0.75 + (0.5 * level)
        familiarity_reduction = 1.15 - (0.3 * level)

        positive = (
            candidate.taste_similarity * self.weights.taste_similarity * familiarity_reduction
            + novelty * self.weights.novelty * novelty_boost
            + artist_unfamiliarity * self.weights.artist_unfamiliarity * novelty_boost
            + genre_exploration * self.weights.genre_exploration * novelty_boost
            + candidate.community_similarity * self.weights.community_similarity
            + serendipity * self.weights.serendipity
            + obscurity * self.weights.obscurity * novelty_boost
        )

        repetition_penalty = 0.0
        if track_plays:
            repetition_penalty += min(0.80, 0.45 + track_plays * 0.10) * level
        if artist_plays >= 5:
            repetition_penalty += min(0.45, (artist_plays - 4) * 0.035) * level
        # Saturation blends recent play frequency with longer-term top-artist and
        # top-track concentration. It does not ban a liked artist; it simply
        # creates room for discovery when the artist is already overrepresented.
        if candidate.artist_saturation >= 0.45:
            repetition_penalty += min(0.35, candidate.artist_saturation * 0.30) * level

        feedback_boost = 0.035 if track.artist_id in liked_artist_ids else 0.0
        language_adjustment = 0.0
        if self.preferences.language_preference is LanguagePreference.ENGLISH_PREFERRED:
            if track.language == "en":
                language_adjustment += 0.025 * track.language_confidence
            elif track.language == "non_english":
                language_adjustment -= 0.12 * track.language_confidence
            elif track.language is None:
                language_adjustment -= 0.015
        final = max(0.0, min(1.0, positive + feedback_boost + language_adjustment - repetition_penalty))

        reasons: list[str] = []
        if track_plays == 0:
            reasons.append("Never played before")
        if artist_plays == 0 and not candidate.artist_known:
            reasons.append("New artist")
        if candidate.artist_saturation >= 0.70:
            reasons.append("Familiar artist deprioritized by saturation")
        if genre_exploration >= 0.5:
            reasons.append("Expands your genre graph")
        if candidate.community_similarity >= 0.75:
            reasons.append("Strong community match")
        if track.artist_id in liked_artist_ids:
            reasons.append("Artist matches your explicit likes")
        if track.language == "en" and track.language_confidence >= 0.55:
            reasons.append("English-language signal")
        if candidate.source.startswith("listenbrainz"):
            reasons.append("ListenBrainz collaborative recommendation")
        if obscurity >= 0.65:
            reasons.append("Lower-exposure pick")

        return RankedTrack(
            track=track,
            score=ScoreBreakdown(
                taste_similarity=round(candidate.taste_similarity, 4),
                novelty=round(novelty, 4),
                artist_unfamiliarity=round(artist_unfamiliarity, 4),
                genre_exploration=round(genre_exploration, 4),
                community_similarity=round(candidate.community_similarity, 4),
                serendipity=round(serendipity, 4),
                obscurity=round(obscurity, 4),
                repetition_penalty=round(repetition_penalty, 4),
                final_score=round(final, 4),
            ),
            reasons=tuple(reasons),
            source=candidate.source,
        )
