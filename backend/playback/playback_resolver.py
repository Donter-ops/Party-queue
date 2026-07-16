from __future__ import annotations

from services.input_resolver import CanonicalSong

from playback.host_provider import HostCapabilities
from playback.playback_strategy import PlaybackStrategy
from playback.provider_match import ProviderMatch
from playback.provider_resolver import ProviderResolver


class PlaybackResolver:
    """Resolve canonical songs into provider-specific playback plans.

    PlaybackResolver coordinates two distinct planning responsibilities. First,
    PlaybackStrategy decides which host provider should be preferred. Second,
    ProviderResolver converts that preference into a concrete provider-specific
    playable identifier. This keeps playback planning modular and future-proof.
    """

    def __init__(
        self,
        playback_strategy: PlaybackStrategy,
        provider_resolver: ProviderResolver,
    ) -> None:
        self.playback_strategy = playback_strategy
        self.provider_resolver = provider_resolver

    def resolve(
        self,
        canonical_song: CanonicalSong,
        host_capabilities: HostCapabilities,
    ) -> ProviderMatch:
        """Return a resolved provider match for the given canonical song."""

        preferred_match = self.playback_strategy.match(canonical_song, host_capabilities)
        return self.provider_resolver.resolve(
            canonical_song=canonical_song,
            preferred_match=preferred_match,
            host_capabilities=host_capabilities,
        )
