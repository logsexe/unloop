from __future__ import annotations

from abc import ABC, abstractmethod

from unloop.domain.models import Candidate, Listen, RankedTrack


class HistoryProvider(ABC):
    @abstractmethod
    async def recent_listens(self, limit: int = 250) -> list[Listen]: ...


class CandidateProvider(ABC):
    @abstractmethod
    async def candidates(self, history: list[Listen], limit: int = 200) -> list[Candidate]: ...


class PlaylistProvider(ABC):
    @abstractmethod
    async def publish_playlist(self, name: str, tracks: list[RankedTrack]) -> str: ...
