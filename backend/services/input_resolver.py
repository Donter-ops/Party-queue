from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from html import unescape
import re
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

from agents.orchestrator_agent import OrchestratorAgent
from providers.base import ProviderSong
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
    """Provider-neutral song candidate returned to the search experience."""

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


@dataclass(slots=True)
class SpotifyFallbackMetadata:
    """Publicly extracted Spotify metadata used when API access is denied."""

    title: str | None
    artist: str | None


class InputResolverService:
    """Resolve one raw user input into canonical song candidates.

    Spotify links are detected before any generic search logic runs. When the
    Spotify catalog API denies direct metadata access, the resolver falls back
    to non-URL-based metadata extraction and normalized search queries so raw
    Spotify URLs never leak into MusicBrainz or downstream queue fields.
    """

    _SPOTIFY_URI_PATTERN = re.compile(r"^spotify:track:(?P<track_id>[A-Za-z0-9]+)$", re.IGNORECASE)
    _TITLE_ARTIST_PATTERN = re.compile(
        r"<title>\s*(?P<title>.*?)\s*-\s*song and lyrics by\s*(?P<artist>.*?)\s*\|\s*Spotify\s*</title>",
        re.IGNORECASE | re.DOTALL,
    )
    _OG_TITLE_PATTERN = re.compile(
        r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\'](?P<value>[^"\']+)["\']',
        re.IGNORECASE,
    )
    _OG_DESCRIPTION_PATTERN = re.compile(
        r'<meta[^>]+property=["\']og:description["\'][^>]+content=["\'](?P<value>[^"\']+)["\']',
        re.IGNORECASE,
    )

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

        normalized_input = self._normalize_input(user_input)

        spotify_id = self._extract_spotify_track_id(normalized_input)
        if spotify_id:
            return ResolvedInput(
                raw_input=normalized_input,
                input_type=InputType.SPOTIFY_URL,
                provider="spotify",
                external_id=spotify_id,
                external_url=self._normalize_spotify_external_url(normalized_input, spotify_id),
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
        """Resolve a Spotify link without ever forwarding the raw URL to search."""

        track_id = resolved_input.external_id or ""
        try:
            spotify_song = self.spotify_provider.get_song(track_id)
        except HTTPError as error:
            if error.code not in {401, 403}:
                raise
            return self._resolve_spotify_fallback(resolved_input=resolved_input, limit=limit)

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

    def _resolve_spotify_fallback(
        self,
        resolved_input: ResolvedInput,
        limit: int,
    ) -> list[CanonicalSong]:
        """Fallback path when Spotify metadata access is denied.

        The fallback never forwards the original Spotify URL to MusicBrainz.
        Instead it extracts public metadata when possible and searches using a
        normalized `title artist` query only.
        """

        track_id = resolved_input.external_id or ""
        metadata = self._extract_spotify_public_metadata(
            track_id=track_id,
            external_url=resolved_input.external_url,
        )

        title = metadata.title
        artist = metadata.artist
        if title and artist:
            normalized_query = self._build_normalized_query(title=title, artist=artist)
            best_match = self._search_spotify_fallback_sources(
                title=title,
                artist=artist,
                query=normalized_query,
                limit=limit,
            )
            chosen_title = best_match.title if best_match is not None else title
            chosen_artist = best_match.artist if best_match is not None else artist
            chosen_confidence = best_match.confidence if best_match and best_match.confidence is not None else 0.6

            return [
                CanonicalSong(
                    title=chosen_title,
                    artist=chosen_artist,
                    provider="spotify_fallback",
                    confidence=chosen_confidence,
                    external_id=track_id,
                    external_url=resolved_input.external_url,
                )
            ]

        return [
            CanonicalSong(
                title=f"Unresolved Spotify track {track_id}",
                artist="Unknown Artist",
                provider="spotify_fallback",
                confidence=0.1,
                external_id=track_id,
                external_url=resolved_input.external_url,
            )
        ]

    def _search_spotify_fallback_sources(
        self,
        *,
        title: str,
        artist: str,
        query: str,
        limit: int,
    ) -> ProviderSong | None:
        """Search fallback catalogs with a normalized query and pick the best match."""

        if not query:
            return None

        musicbrainz_matches = self._search_musicbrainz(query=query, limit=limit).matches
        youtube_matches = self.youtube_provider.search(query)[:limit]

        candidates: list[ProviderSong] = [*musicbrainz_matches, *youtube_matches]
        if not candidates:
            return None

        candidates.sort(
            key=lambda candidate: self._score_fallback_candidate(
                title=title,
                artist=artist,
                candidate=candidate,
            ),
            reverse=True,
        )
        return candidates[0]

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

    def _extract_spotify_public_metadata(
        self,
        *,
        track_id: str,
        external_url: str | None,
    ) -> SpotifyFallbackMetadata:
        """Extract public title/artist metadata from the Spotify track page."""

        request_url = external_url or f"https://open.spotify.com/track/{track_id}"
        request = Request(
            request_url,
            headers={"User-Agent": "PartyQueue/1.0"},
            method="GET",
        )
        try:
            with urlopen(request, timeout=SpotifyProvider.REQUEST_TIMEOUT_SECONDS) as response:
                html = response.read().decode("utf-8", errors="replace")
        except Exception:
            return SpotifyFallbackMetadata(title=None, artist=None)

        title_match = self._TITLE_ARTIST_PATTERN.search(html)
        if title_match is not None:
            return SpotifyFallbackMetadata(
                title=unescape(title_match.group("title")).strip() or None,
                artist=unescape(title_match.group("artist")).strip() or None,
            )

        title = self._extract_meta_content(self._OG_TITLE_PATTERN, html)
        description = self._extract_meta_content(self._OG_DESCRIPTION_PATTERN, html)
        artist = self._extract_artist_from_description(description, title)
        return SpotifyFallbackMetadata(title=title, artist=artist)

    @staticmethod
    def _extract_meta_content(pattern: re.Pattern[str], html: str) -> str | None:
        """Extract one HTML meta tag content value."""

        match = pattern.search(html)
        if match is None:
            return None
        value = unescape(match.group("value")).strip()
        return value or None

    @staticmethod
    def _extract_artist_from_description(description: str | None, title: str | None) -> str | None:
        """Derive artist metadata from a public Spotify description string."""

        if not description:
            return None
        parts = [part.strip() for part in re.split(r"[·|]", description) if part.strip()]
        ignored = {"song", "album", "spotify"}
        filtered_parts = [
            part
            for part in parts
            if part.lower() not in ignored and part != title and not part.isdigit()
        ]
        return filtered_parts[0] if filtered_parts else None

    @staticmethod
    def _build_normalized_query(*, title: str, artist: str) -> str:
        """Build a non-URL fallback query for secondary catalogs."""

        return " ".join(part for part in (title.strip(), artist.strip()) if part).strip()

    @staticmethod
    def _score_fallback_candidate(
        *,
        title: str,
        artist: str,
        candidate: ProviderSong,
    ) -> float:
        """Score fallback search candidates against extracted Spotify metadata."""

        normalized_title = InputResolverService._normalize_text(title)
        normalized_artist = InputResolverService._normalize_text(artist)
        candidate_title = InputResolverService._normalize_text(candidate.title)
        candidate_artist = InputResolverService._normalize_text(candidate.artist)

        title_score = InputResolverService._similarity(normalized_title, candidate_title)
        artist_score = InputResolverService._similarity(normalized_artist, candidate_artist)
        provider_confidence = candidate.confidence or 0.0
        return (title_score * 0.45) + (artist_score * 0.4) + (provider_confidence * 0.15)

    @staticmethod
    def _similarity(left: str, right: str) -> float:
        """Return a small deterministic similarity score for fallback matching."""

        if not left or not right:
            return 0.0
        if left == right:
            return 1.0
        left_tokens = set(left.split())
        right_tokens = set(right.split())
        if not left_tokens or not right_tokens:
            return 0.0
        return len(left_tokens & right_tokens) / len(left_tokens | right_tokens)

    @staticmethod
    def _normalize_text(value: str) -> str:
        """Normalize text for safe fallback comparisons."""

        lowered = value.strip().lower()
        lowered = re.sub(r"\([^)]*\)", " ", lowered)
        lowered = re.sub(r"[^a-z0-9]+", " ", lowered)
        return " ".join(lowered.split())

    @staticmethod
    def _normalize_input(user_input: str) -> str:
        """Trim surrounding whitespace without altering provider IDs."""

        return user_input.strip()

    @classmethod
    def _extract_spotify_track_id(cls, user_input: str) -> str | None:
        """Extract a Spotify track identifier from URL or URI forms."""

        normalized_input = user_input.strip()
        uri_match = cls._SPOTIFY_URI_PATTERN.match(normalized_input)
        if uri_match is not None:
            return uri_match.group("track_id")

        parsed = urlparse(normalized_input)
        netloc = parsed.netloc.strip().lower()
        if netloc != "open.spotify.com":
            return None

        path_parts = [part.strip() for part in parsed.path.split("/") if part.strip()]

        # Finde das Segment "track", egal an welcher Position es steht
        try:
            track_index = next(i for i, part in enumerate(path_parts) if part.lower() == "track")
        except StopIteration:
            return None

        # Das nächste Segment muss die Track-ID sein
        if track_index + 1 >= len(path_parts):
            return None

        track_id = path_parts[track_index + 1].rstrip("/")
        return track_id or None
    @staticmethod
    def _normalize_spotify_external_url(user_input: str, track_id: str) -> str:
        """Return a canonical Spotify track URL for downstream systems."""

        if user_input.lower().startswith("spotify:track:"):
            return f"https://open.spotify.com/track/{track_id}"

        parsed = urlparse(user_input.strip())
        scheme = parsed.scheme.lower() if parsed.scheme else "https"
        return f"{scheme}://open.spotify.com/track/{track_id}"

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
        """Extract an Apple Music track identifier when present."""

        parsed = urlparse(user_input)
        if "music.apple.com" not in parsed.netloc:
            return None

        query_params = parse_qs(parsed.query)
        if query_params.get("i"):
            return query_params["i"][0]

        path_parts = [part for part in parsed.path.split("/") if part]
        return path_parts[-1] if path_parts else None
