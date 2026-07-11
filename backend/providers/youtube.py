from __future__ import annotations

from providers.base import MusicProvider, ProviderSong


class YouTubeProvider(MusicProvider):
    def search(self, query: str) -> list[ProviderSong]:
        raise NotImplementedError("YouTube provider is not implemented yet.")

    def resolve(self, url: str) -> ProviderSong:
        raise NotImplementedError("YouTube provider is not implemented yet.")

    def get_song(self, provider_id: str) -> ProviderSong:
        raise NotImplementedError("YouTube provider is not implemented yet.")
