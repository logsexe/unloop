from __future__ import annotations

from unloop.domain.models import Candidate, Listen
from unloop.providers.base import CandidateProvider


class CompositeCandidateProvider(CandidateProvider):
    def __init__(self, providers: list[CandidateProvider]) -> None:
        self.providers = providers

    async def candidates(self, history: list[Listen], limit: int = 200) -> list[Candidate]:
        merged: dict[str, Candidate] = {}
        per_provider = max(40, limit // max(1, len(self.providers)))
        for provider in self.providers:
            try:
                items = await provider.candidates(history, limit=per_provider)
            except Exception:
                # A discovery source should degrade independently, not take down the batch.
                continue
            for item in items:
                existing = merged.get(item.track.id)
                if existing is None or item.source_confidence > existing.source_confidence:
                    merged[item.track.id] = item
        return list(merged.values())[:limit]
