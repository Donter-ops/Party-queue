from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(slots=True)
class ProviderSong:
    """Provider-neutral representation of a resolved external song."""

    provider: str
    provider_id: str
    title: str
    artist: str
    external_url: str | None = None
    confidence: float | None = None


class MusicProvider(ABC):
    """Abstract contract implemented by future music provider adapters."""

    @abstractmethod
    def search(self, query: str) -> list[ProviderSong]:
        """Search the provider catalog for a user query."""
        raise NotImplementedError

    @abstractmethod
    def resolve(self, url: str) -> ProviderSong:
        """Resolve a provider-specific URL into a normalized provider song."""
        raise NotImplementedError

    @abstractmethod
    def get_song(self, provider_id: str) -> ProviderSong:
        """Fetch a single provider song by provider-native identifier."""
        raise NotImplementedError
