from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Iterable

from unloop.domain.models import ArtistMetadata, ArtistSaturation, TasteCluster


# Transparent parent-cluster taxonomy. These are not user labels or an ML model;
# they simply make open metadata easier to navigate and explain in the UI.
CLUSTER_TERMS: dict[str, tuple[str, ...]] = {
    "Electronic / Dance": (
        "electronic", "house", "techno", "dance", "edm", "ambient", "garage",
        "electronica", "downtempo", "trance", "drum and bass", "dubstep", "idm",
    ),
    "Hip-Hop / Rap": (
        "hip hop", "hip-hop", "rap", "trap", "grime", "drill", "cloud rap",
    ),
    "R&B / Soul": (
        "r&b", "rhythm and blues", "soul", "neo soul", "funk",
    ),
    "Rock / Alternative": (
        "rock", "alternative", "indie rock", "punk", "post-punk", "shoegaze",
        "metal", "grunge", "emo",
    ),
    "Pop": (
        "pop", "synthpop", "dance-pop", "indie pop", "electropop",
    ),
    "Country / Folk": (
        "country", "folk", "americana", "bluegrass", "singer-songwriter",
    ),
    "Jazz / Blues": (
        "jazz", "blues", "bebop", "swing",
    ),
    "Classical / Contemporary": (
        "classical", "modern classical", "contemporary classical", "orchestral",
    ),
    "Global / Regional": (
        "afrobeats", "afrobeat", "latin", "reggae", "dancehall", "k-pop", "j-pop",
        "bossa nova", "samba", "flamenco",
    ),
}


def _normalize(value: str) -> str:
    return " ".join(value.casefold().replace("_", " ").replace("-", "-").split())


def classify_tag(tag: str) -> str | None:
    normalized = _normalize(tag)
    for cluster, terms in CLUSTER_TERMS.items():
        if any(term == normalized or term in normalized for term in terms):
            return cluster
    return None


def build_taste_clusters(metadata: Iterable[ArtistMetadata]) -> list[TasteCluster]:
    weights: Counter[str] = Counter()
    evidence: dict[str, Counter[str]] = defaultdict(Counter)

    for artist in metadata:
        # Genres are curated, so give them more weight than free-form tags.
        for genre in artist.genres:
            cluster = classify_tag(genre)
            if cluster:
                weights[cluster] += 3
                evidence[cluster][genre] += 3
        for tag, count in artist.tags.items():
            cluster = classify_tag(tag)
            if cluster:
                contribution = max(1, min(int(count), 10))
                weights[cluster] += contribution
                evidence[cluster][tag] += contribution

    total = sum(weights.values())
    if total == 0:
        return []

    clusters = [
        TasteCluster(
            name=name,
            weight=round(weight / total, 4),
            evidence=tuple(term for term, _ in evidence[name].most_common(6)),
        )
        for name, weight in weights.most_common()
    ]
    return clusters


def calculate_artist_saturation(
    *,
    recent_artist_counts: Counter[str],
    recent_artist_names: dict[str, str],
    top_track_artist_counts: Counter[str],
    top_artist_ranks: dict[str, int],
    limit: int = 20,
) -> list[ArtistSaturation]:
    artist_ids = set(recent_artist_counts) | set(top_track_artist_counts) | set(top_artist_ranks)
    result: list[ArtistSaturation] = []

    for artist_id in artist_ids:
        recent = recent_artist_counts[artist_id]
        top_tracks = top_track_artist_counts[artist_id]
        rank = top_artist_ranks.get(artist_id)

        # Transparent 0-100 heuristic. Recency matters most; repeated presence in
        # the user's top tracks and top artists adds longer-term saturation.
        recent_component = min(55.0, recent * 7.0)
        track_component = min(30.0, top_tracks * 8.0)
        rank_component = 0.0 if rank is None else max(0.0, 15.0 - (rank - 1) * 0.75)
        score = min(100.0, recent_component + track_component + rank_component)

        if score < 15:
            status = "open"
        elif score < 45:
            status = "warm"
        elif score < 70:
            status = "cool"
        else:
            status = "saturated"

        reasons: list[str] = []
        if recent >= 3:
            reasons.append(f"{recent} recent plays loaded")
        if top_tracks >= 2:
            reasons.append(f"{top_tracks} tracks in your current top-track sample")
        if rank is not None and rank <= 10:
            reasons.append(f"top-artist rank #{rank}")

        result.append(
            ArtistSaturation(
                artist_id=artist_id,
                artist_name=recent_artist_names.get(artist_id, artist_id),
                score=round(score, 1),
                status=status,
                recent_plays=recent,
                top_track_count=top_tracks,
                top_artist_rank=rank,
                reasons=tuple(reasons),
            )
        )

    result.sort(key=lambda item: item.score, reverse=True)
    return result[:limit]
