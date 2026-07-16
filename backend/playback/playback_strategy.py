from __future__ import annotations

from services.input_resolver import CanonicalSong

from playback.host_provider import HostCapabilities, HostProvider
from playback.provider_match import ProviderMatch


class PlaybackStrategy:
    """Provider-independent planner for future host playback.

    The strategy defines how PartyQueue should map a canonical song to a host
    playback provider based on local capabilities. It never talks to Spotify,
    YouTube Music, or Apple Music directly; it only returns a structured
    ProviderMatch that future provider-specific execution layers can consume.
    """

    def match(
        self,
        canonical_song: CanonicalSong,
        host_capabilities: HostCapabilities,
    ) -> ProviderMatch:
        """Return a provider match plan for the given canonical song."""

        direct_provider = self._map_canonical_provider(canonical_song.provider)
        supported = set(host_capabilities.supported_providers)

        if direct_provider is not None and direct_provider in supported:
            return ProviderMatch(
                provider=direct_provider.value,
                provider_track_id=canonical_song.external_id,
                confidence=canonical_song.confidence,
                fallback_provider=self._select_fallback_provider(
                    host_capabilities,
                    excluding=direct_provider,
                ),
            )

        planned_provider = host_capabilities.preferred_provider
        if planned_provider is None and host_capabilities.supported_providers:
            planned_provider = host_capabilities.supported_providers[0]

        if planned_provider is None:
            return ProviderMatch(
                provider=None,
                provider_track_id=canonical_song.external_id,
                confidence=0.0,
                fallback_provider=None,
            )

        return ProviderMatch(
            provider=planned_provider.value,
            provider_track_id=canonical_song.external_id,
            confidence=min(canonical_song.confidence, 0.6),
            fallback_provider=self._select_fallback_provider(
                host_capabilities,
                excluding=planned_provider,
            ),
        )

    @staticmethod
    def _map_canonical_provider(provider: str) -> HostProvider | None:
        """Map canonical provider names onto future host providers."""

        if provider == "spotify":
            return HostProvider.SPOTIFY
        if provider == "youtube":
            return HostProvider.YOUTUBE_MUSIC
        if provider == "apple_music":
            return HostProvider.APPLE_MUSIC
        return None

    @staticmethod
    def _select_fallback_provider(
        host_capabilities: HostCapabilities,
        *,
        excluding: HostProvider | None,
    ) -> str | None:
        """Return the next available host provider for fallback planning."""

        for provider in host_capabilities.supported_providers:
            if provider != excluding:
                return provider.value
        return None
