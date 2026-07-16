from __future__ import annotations

from providers.spotify import SpotifyProvider
from providers.youtube import YouTubeProvider
from services.input_resolver import CanonicalSong

from playback.host_provider import HostCapabilities, HostProvider
from playback.provider_match import ProviderMatch


class ProviderResolver:
    """Resolve canonical songs into provider-specific playable identifiers.

    This resolver is the last planning step before future playback execution.
    It receives a canonical song plus the provider preference selected by the
    playback strategy and produces a concrete ProviderMatch. Real provider APIs
    can replace the placeholder logic later without changing PlaybackResolver or
    PlaybackEngine.
    """

    def __init__(
        self,
        spotify_provider: SpotifyProvider,
        youtube_provider: YouTubeProvider,
    ) -> None:
        self.spotify_provider = spotify_provider
        self.youtube_provider = youtube_provider

    def resolve(
        self,
        canonical_song: CanonicalSong,
        preferred_match: ProviderMatch,
        host_capabilities: HostCapabilities,
    ) -> ProviderMatch:
        """Resolve a canonical song into a provider-specific playable item."""

        target_provider = self._resolve_target_provider(preferred_match, host_capabilities)
        if target_provider is None:
            return ProviderMatch(
                provider=None,
                provider_track_id=None,
                confidence=0.0,
                fallback_provider=preferred_match.fallback_provider,
                resolved_title=canonical_song.title,
                resolved_artist=canonical_song.artist,
            )

        if target_provider is HostProvider.SPOTIFY:
            return self._resolve_spotify(canonical_song, preferred_match)

        if target_provider is HostProvider.YOUTUBE_MUSIC:
            return self._resolve_youtube(canonical_song, preferred_match)

        return self._resolve_apple_music(canonical_song, preferred_match)

    def _resolve_spotify(
        self,
        canonical_song: CanonicalSong,
        preferred_match: ProviderMatch,
    ) -> ProviderMatch:
        """Build a Spotify-oriented provider match with placeholder resolution."""

        _ = self.spotify_provider
        if canonical_song.provider == "spotify":
            track_id = canonical_song.external_id
            confidence = max(preferred_match.confidence, canonical_song.confidence)
        else:
            track_id = self._build_placeholder_track_id("spotify", canonical_song)
            confidence = min(preferred_match.confidence, 0.55)

        return ProviderMatch(
            provider=HostProvider.SPOTIFY.value,
            provider_track_id=track_id,
            confidence=confidence,
            fallback_provider=preferred_match.fallback_provider,
            resolved_title=canonical_song.title,
            resolved_artist=canonical_song.artist,
        )

    def _resolve_youtube(
        self,
        canonical_song: CanonicalSong,
        preferred_match: ProviderMatch,
    ) -> ProviderMatch:
        """Build a YouTube Music-oriented provider match with placeholder resolution."""

        _ = self.youtube_provider
        if canonical_song.provider == "youtube":
            track_id = canonical_song.external_id
            confidence = max(preferred_match.confidence, canonical_song.confidence)
        else:
            track_id = self._build_placeholder_track_id("youtube_music", canonical_song)
            confidence = min(preferred_match.confidence, 0.55)

        return ProviderMatch(
            provider=HostProvider.YOUTUBE_MUSIC.value,
            provider_track_id=track_id,
            confidence=confidence,
            fallback_provider=preferred_match.fallback_provider,
            resolved_title=canonical_song.title,
            resolved_artist=canonical_song.artist,
        )

    def _resolve_apple_music(
        self,
        canonical_song: CanonicalSong,
        preferred_match: ProviderMatch,
    ) -> ProviderMatch:
        """Build an Apple Music-oriented provider match placeholder."""

        if canonical_song.provider == "apple_music":
            track_id = canonical_song.external_id
            confidence = max(preferred_match.confidence, canonical_song.confidence)
        else:
            track_id = self._build_placeholder_track_id("apple_music", canonical_song)
            confidence = min(preferred_match.confidence, 0.5)

        return ProviderMatch(
            provider=HostProvider.APPLE_MUSIC.value,
            provider_track_id=track_id,
            confidence=confidence,
            fallback_provider=preferred_match.fallback_provider,
            resolved_title=canonical_song.title,
            resolved_artist=canonical_song.artist,
        )

    @staticmethod
    def _resolve_target_provider(
        preferred_match: ProviderMatch,
        host_capabilities: HostCapabilities,
    ) -> HostProvider | None:
        """Map the preferred strategy output to an available host provider."""

        supported = {provider.value: provider for provider in host_capabilities.supported_providers}
        if preferred_match.provider and preferred_match.provider in supported:
            return supported[preferred_match.provider]

        if preferred_match.fallback_provider and preferred_match.fallback_provider in supported:
            return supported[preferred_match.fallback_provider]

        if host_capabilities.preferred_provider is not None:
            return host_capabilities.preferred_provider

        return host_capabilities.supported_providers[0] if host_capabilities.supported_providers else None

    @staticmethod
    def _build_placeholder_track_id(provider: str, canonical_song: CanonicalSong) -> str:
        """Create a stable placeholder playable identifier for later providers."""

        normalized_title = canonical_song.title.lower().replace(" ", "-")
        normalized_artist = canonical_song.artist.lower().replace(" ", "-")
        return f"{provider}:search:{normalized_artist}:{normalized_title}"
