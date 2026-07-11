from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True)
class ProviderSong:
    provider: str
    provider_id: str
    title: str
    artist: str
    external_url: str | None = None


class MusicProvider(ABC):
    @abstractmethod
    def search(self, query: str) -> list[ProviderSong]:
        raise NotImplementedError

    @abstractmethod
    def resolve(self, url: str) -> ProviderSong:
        raise NotImplementedError

    @abstractmethod
    def get_song(self, provider_id: str) -> ProviderSong:
        raise NotImplementedError
