from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from urllib.parse import parse_qs, urlparse

from agents.orchestrator_agent import OrchestratorAgent
from providers.spotify import SpotifyProvider
from providers.youtube import YouTubeProvider
from schemas.search import SearchResultResponse
from tools.search_models import SearchRequest, SearchResult


class InputType(StrEnum):
    """Supported classes of user-provided song input."""

    SEARCH_QUERY = "search_query"
    SPOTIFY_URL = "spotify_url"
    YOUTUBE_URL = "youtube_url"
    APPLE_URL = "apple_url"


@dataclass(slots=True)
class CanonicalSong:
    """Provider-neutral song candidate returned to the search experience.

    The universal input pipeline always normalizes user input into this shape so
    the frontend can remain unaware of whether the origin was free text, a
    Spotify URL, a YouTube URL, or an Apple Music URL.
    """

    title: str
    artist: str
    provider: str
    confidence: float
    external_id: str
    external_url: str | None = None

    def to_response(self) -> SearchResultResponse:
        """Convert the canonical song into the API response model."""

        return SearchResultResponse(
            title=self.title,
            artist=self.artist,
            provider=self.provider,
            confidence=self.confidence,
            external_id=self.external_id,
            external_url=self.external_url,
        )


@dataclass(slots=True)
class ResolvedInput:
    """Structured result of detecting the user's raw song input."""

    raw_input: str
    input_type: InputType
    provider: str
    external_id: str | None = None
    external_url: str | None = None


class InputResolverService:
    """Resolve one raw user input into canonical song candidates.

    This service is the entry point for the universal song input pipeline. It
    detects input type first, then routes the request through the existing
    orchestration layer. Free text keeps using MusicBrainz exactly as before,
    while provider URLs are normalized into canonical results without changing
    the frontend search experience or the downstream queue flow.
    """

    def __init__(
        self,
        orchestrator_agent: OrchestratorAgent,
        spotify_provider: SpotifyProvider,
        youtube_provider: YouTubeProvider,
    ) -> None:
        self.orchestrator_agent = orchestrator_agent
        self.spotify_provider = spotify_provider
        self.youtube_provider = youtube_provider

    def resolve(self, user_input: str, limit: int = 5) -> list[CanonicalSong]:
        """Return canonical song candidates for free text or provider URLs."""

        resolved_input = self.detect_input(user_input)

        if resolved_input.input_type is InputType.SEARCH_QUERY:
            search_result = self._search_musicbrainz(query=resolved_input.raw_input, limit=limit)
            return self._canonicalize_search_result(search_result)

        if resolved_input.input_type is InputType.SPOTIFY_URL:
            return self._resolve_spotify_input(resolved_input, limit=limit)

        if resolved_input.input_type is InputType.YOUTUBE_URL:
            return self._resolve_youtube_input(resolved_input, limit=limit)

        return self._resolve_apple_input(resolved_input, limit=limit)

    def detect_input(self, user_input: str) -> ResolvedInput:
        """Detect whether the incoming string is text or a supported URL."""

        normalized_input = user_input.strip()

        spotify_id = self._extract_spotify_track_id(normalized_input)
        if spotify_id:
            return ResolvedInput(
                raw_input=normalized_input,
                input_type=InputType.SPOTIFY_URL,
                provider="spotify",
                external_id=spotify_id,
                external_url=normalized_input,
            )

        youtube_id = self._extract_youtube_video_id(normalized_input)
        if youtube_id:
            return ResolvedInput(
                raw_input=normalized_input,
                input_type=InputType.YOUTUBE_URL,
                provider="youtube",
                external_id=youtube_id,
                external_url=normalized_input,
            )

        apple_id = self._extract_apple_track_id(normalized_input)
        if apple_id:
            return ResolvedInput(
                raw_input=normalized_input,
                input_type=InputType.APPLE_URL,
                provider="apple_music",
                external_id=apple_id,
                external_url=normalized_input,
            )

        return ResolvedInput(
            raw_input=normalized_input,
            input_type=InputType.SEARCH_QUERY,
            provider="musicbrainz",
        )

    def _resolve_spotify_input(
        self,
        resolved_input: ResolvedInput,
        limit: int,
    ) -> list[CanonicalSong]:
        """Resolve a Spotify link into canonical song candidates.

        The Spotify provider remains a placeholder, so the resolver currently
        extracts the track identifier, issues a MusicBrainz search request using
        the available deterministic metadata, and falls back to a canonical
        placeholder result when no MusicBrainz match is found.
        """

        try:
            spotify_song = self.spotify_provider.resolve(resolved_input.raw_input)
        except (RuntimeError, ValueError):
            spotify_song = None

        if spotify_song is not None:
            return [
                CanonicalSong(
                    title=spotify_song.title,
                    artist=spotify_song.artist,
                    provider="spotify",
                    confidence=spotify_song.confidence or 1.0,
                    external_id=spotify_song.provider_id,
                    external_url=spotify_song.external_url or resolved_input.external_url,
                )
            ]

        search_result = self._search_musicbrainz(query=resolved_input.external_id or "", limit=limit)
        if search_result.matches:
            return self._canonicalize_search_result(
                search_result,
                provider_override="spotify",
                external_id_override=resolved_input.external_id,
                external_url_override=resolved_input.external_url,
            )

        return [
            CanonicalSong(
                title=f"Spotify Track {resolved_input.external_id}",
                artist="Unknown Artist",
                provider="spotify",
                confidence=0.35,
                external_id=resolved_input.external_id or "",
                external_url=resolved_input.external_url,
            )
        ]

    def _resolve_youtube_input(
        self,
        resolved_input: ResolvedInput,
        limit: int,
    ) -> list[CanonicalSong]:
        """Resolve a YouTube or YouTube Music link into canonical song candidates."""

        try:
            youtube_song = self.youtube_provider.resolve(resolved_input.raw_input)
        except (RuntimeError, ValueError):
            youtube_song = None

        if youtube_song is not None:
            return [
                CanonicalSong(
                    title=youtube_song.title,
                    artist=youtube_song.artist,
                    provider="youtube",
                    confidence=youtube_song.confidence or 1.0,
                    external_id=youtube_song.provider_id,
                    external_url=youtube_song.external_url or resolved_input.external_url,
                )
            ]

        search_result = self._search_musicbrainz(query=resolved_input.external_id or "", limit=limit)
        if search_result.matches:
            return self._canonicalize_search_result(
                search_result,
                provider_override="youtube",
                external_id_override=resolved_input.external_id,
                external_url_override=resolved_input.external_url,
            )

        return [
            CanonicalSong(
                title=f"YouTube Track {resolved_input.external_id}",
                artist="Unknown Artist",
                provider="youtube",
                confidence=0.35,
                external_id=resolved_input.external_id or "",
                external_url=resolved_input.external_url,
            )
        ]

    def _resolve_apple_input(
        self,
        resolved_input: ResolvedInput,
        limit: int,
    ) -> list[CanonicalSong]:
        """Prepare Apple Music URL handling without a provider implementation."""

        search_result = self._search_musicbrainz(query=resolved_input.external_id or "", limit=limit)
        if search_result.matches:
            return self._canonicalize_search_result(
                search_result,
                provider_override="apple_music",
                external_id_override=resolved_input.external_id,
                external_url_override=resolved_input.external_url,
            )

        return [
            CanonicalSong(
                title=f"Apple Music Track {resolved_input.external_id}",
                artist="Unknown Artist",
                provider="apple_music",
                confidence=0.3,
                external_id=resolved_input.external_id or "",
                external_url=resolved_input.external_url,
            )
        ]

    def _search_musicbrainz(self, query: str, limit: int) -> SearchResult:
        """Execute the existing MusicBrainz-backed search through the agent."""

        request = SearchRequest(
            query=query.strip(),
            provider="musicbrainz",
            limit=limit,
            source_hint="input_resolver",
        )
        return self.orchestrator_agent.search(request)

    def _canonicalize_search_result(
        self,
        result: SearchResult,
        *,
        provider_override: str | None = None,
        external_id_override: str | None = None,
        external_url_override: str | None = None,
    ) -> list[CanonicalSong]:
        """Normalize a search result into canonical songs."""

        canonical_provider = provider_override or result.provider
        return [
            CanonicalSong(
                title=match.title,
                artist=match.artist,
                provider=canonical_provider,
                confidence=match.confidence if match.confidence is not None else result.confidence,
                external_id=external_id_override or match.provider_id,
                external_url=external_url_override or match.external_url,
            )
            for match in result.matches
        ]

    @staticmethod
    def _extract_spotify_track_id(user_input: str) -> str | None:
        """Extract a Spotify track identifier from URL or URI forms."""

        if user_input.startswith("spotify:track:"):
            track_id = user_input.removeprefix("spotify:track:").strip()
            return track_id or None

        parsed = urlparse(user_input)
        if "open.spotify.com" not in parsed.netloc:
            return None

        path_parts = [part for part in parsed.path.split("/") if part]
        if len(path_parts) >= 2 and path_parts[0] == "track":
            return path_parts[1]
        return None

    @staticmethod
    def _extract_youtube_video_id(user_input: str) -> str | None:
        """Extract a YouTube or YouTube Music video identifier."""

        parsed = urlparse(user_input)
        if parsed.netloc == "youtu.be":
            candidate = parsed.path.lstrip("/").split("/", 1)[0]
            return candidate or None

        if parsed.netloc not in {"music.youtube.com", "www.youtube.com", "youtube.com"}:
            return None

        query_params = parse_qs(parsed.query)
        video_id = query_params.get("v", [None])[0]
        if video_id:
            return video_id

        path_parts = [part for part in parsed.path.split("/") if part]
        if len(path_parts) >= 2 and path_parts[0] in {"embed", "shorts"}:
            return path_parts[1]
        return None

    @staticmethod
    def _extract_apple_track_id(user_input: str) -> str | None:
        """Extract an Apple Music track identifier when present.

        Apple Music URLs may encode a track id either in the ``i`` query
        parameter or in the trailing path segment. The resolver supports both so
        the architecture is ready for a future Apple Music provider.
        """

        parsed = urlparse(user_input)
        if "music.apple.com" not in parsed.netloc:
            return None

        query_params = parse_qs(parsed.query)
        if query_params.get("i"):
            return query_params["i"][0]

        path_parts = [part for part in parsed.path.split("/") if part]
        return path_parts[-1] if path_parts else None
