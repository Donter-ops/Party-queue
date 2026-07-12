from __future__ import annotations

from providers.base import MusicProvider, ProviderSong


class SpotifyProvider(MusicProvider):
    """Placeholder Spotify adapter for future provider-specific logic."""

    def search(self, query: str) -> list[ProviderSong]:
        raise NotImplementedError("Spotify provider is not implemented yet.")

    def resolve(self, url: str) -> ProviderSong:
        raise NotImplementedError("Spotify provider is not implemented yet.")

    def get_song(self, provider_id: str) -> ProviderSong:
        raise NotImplementedError("Spotify provider is not implemented yet.")
