from __future__ import annotations

import re
from dataclasses import dataclass

_NON_LATIN = re.compile(r"[^\x00-\x7F]")
_COMMON_ENGLISH = {
    "the", "and", "you", "me", "my", "your", "love", "with", "without", "in", "on",
    "for", "to", "of", "is", "are", "we", "us", "all", "time", "night", "day", "home",
    "heart", "down", "up", "away", "again", "back", "never", "always", "one", "more",
}

@dataclass(frozen=True, slots=True)
class LanguageGuess:
    language: str | None
    confidence: float

def guess_track_language(title: str) -> LanguageGuess:
    """Best-effort language hint from title text only.

    Spotify does not expose canonical track language. We intentionally return low
    confidence for ambiguous Latin-script titles instead of pretending certainty.
    """
    if not title.strip():
        return LanguageGuess(None, 0.0)
    if _NON_LATIN.search(title):
        return LanguageGuess("non_english", 0.92)
    words = [w.lower() for w in re.findall(r"[A-Za-z']+", title)]
    if not words:
        return LanguageGuess(None, 0.0)
    english_hits = sum(1 for w in words if w in _COMMON_ENGLISH)
    if english_hits:
        confidence = min(0.92, 0.58 + 0.10 * english_hits)
        return LanguageGuess("en", confidence)
    # Latin script is not enough to assert English. Keep it unknown so
    # ENGLISH_PREFERRED can softly penalize rather than hard-exclude it.
    return LanguageGuess(None, 0.25)
