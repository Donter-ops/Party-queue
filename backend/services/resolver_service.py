from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
import logging
import re

import schemas
from agents.orchestrator_agent import OrchestratorAgent
from decision.decision import AgentDecision
from playback.host_provider import HostCapabilities, HostProvider
from providers.base import ProviderSong
from providers.spotify import SpotifyProvider
from providers.youtube import YouTubeProvider

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class SongResolutionResult:
    """Resolved queue payload plus host-playback metadata.

    The API still accepts the same SongCreate payload, but the persistence layer
    can now store provider-specific playback details derived from the current
    host capabilities. This keeps queue insertion compatible while allowing the
    queued item to become immediately playable.
    """

    song: schemas.SongCreate
    resolution_confidence: float | None = None
    resolution_reason: str | None = None


class SongResolverService:
    """Service wrapper around the orchestration layer for song preparation.

    The resolver is the compatibility boundary between today's synchronous song
    creation flow and tomorrow's richer decision-driven agent workflows.
    """

    YOUTUBE_CONFIDENCE_THRESHOLD = 0.75
    NEGATIVE_MARKERS = (
        "live",
        "cover",
        "remix",
        "nightcore",
        "slowed",
        "sped up",
        "karaoke",
        "instrumental",
        "fan edit",
    )

    def __init__(
        self,
        orchestrator_agent: OrchestratorAgent,
        host_capabilities: HostCapabilities,
        spotify_provider: SpotifyProvider,
        youtube_provider: YouTubeProvider,
    ) -> None:
        self.orchestrator_agent = orchestrator_agent
        self.host_capabilities = host_capabilities
        self.spotify_provider = spotify_provider
        self.youtube_provider = youtube_provider
        self._playable_cache: dict[tuple[str, str, str], SongResolutionResult] = {}

    def resolve_song(self, song: schemas.SongCreate) -> schemas.SongCreate:
        """Delegate song preparation to the orchestrator agent.

        The orchestrator now returns a decision object. Current functionality is
        preserved by keeping the original song payload unchanged after the
        decision has been recorded.
        """
        return self.resolve_song_for_queue(song).song

    def resolve_song_for_queue(self, song: schemas.SongCreate) -> SongResolutionResult:
        """Resolve a queue item into the host's playable provider when possible."""

        _decision = self.decide_song(song)
        normalized_song, source_metadata = self._normalize_source_song(song)
        return self._resolve_host_playable_song(normalized_song, source_metadata)

    def decide_song(self, song: schemas.SongCreate) -> AgentDecision:
        """Return the structured orchestration decision for the incoming song."""
        return self.orchestrator_agent.decide(song)

    def _normalize_source_song(self, song: schemas.SongCreate) -> tuple[schemas.SongCreate, ProviderSong | None]:
        """Refresh direct provider URLs with authoritative provider metadata."""

        if song.source == "spotify" and song.external_url:
            try:
                spotify_song = self.spotify_provider.resolve(song.external_url)
            except (RuntimeError, ValueError):
                return song, None
            return (
                schemas.SongCreate(
                    title=spotify_song.title,
                    artist=spotify_song.artist,
                    added_by=song.added_by,
                    source="spotify",
                    external_url=spotify_song.external_url or song.external_url,
                ),
                spotify_song,
            )

        if song.source == "youtube" and song.external_url:
            try:
                youtube_song = self.youtube_provider.resolve(song.external_url)
            except (RuntimeError, ValueError):
                return song, None
            return (
                schemas.SongCreate(
                    title=youtube_song.title,
                    artist=youtube_song.artist,
                    added_by=song.added_by,
                    source="youtube",
                    external_url=youtube_song.external_url or song.external_url,
                ),
                youtube_song,
            )

        return song, None

    def _resolve_host_playable_song(
        self,
        song: schemas.SongCreate,
        source_metadata: ProviderSong | None,
    ) -> SongResolutionResult:
        """Map a song onto the active host provider without changing APIs."""

        target_provider = self.host_capabilities.preferred_provider
        if target_provider is HostProvider.YOUTUBE_MUSIC:
            return self._resolve_youtube_playable_song(song, source_metadata)
        if target_provider is HostProvider.SPOTIFY:
            return self._resolve_spotify_playable_song(song)
        return SongResolutionResult(song=song)

    def _resolve_youtube_playable_song(
        self,
        song: schemas.SongCreate,
        source_metadata: ProviderSong | None,
    ) -> SongResolutionResult:
        """Resolve any supported source into a playable YouTube-backed queue item."""

        if song.source == "youtube" and song.external_url:
            return SongResolutionResult(
                song=song,
                resolution_confidence=1.0,
                resolution_reason="Direct YouTube URL provided.",
            )

        cache_key = self._build_cache_key(song, target="youtube")
        cached_result = self._playable_cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        search_query = self._build_youtube_query(song)
        matches = self.youtube_provider.search(search_query)
        best_candidate = self._select_best_youtube_candidate(song=song, source_metadata=source_metadata, matches=matches)
        if best_candidate is None or best_candidate.score < self.YOUTUBE_CONFIDENCE_THRESHOLD:
            fallback_result = SongResolutionResult(
                song=song,
                resolution_confidence=0.0,
                resolution_reason="No reliable match",
            )
            self._log_youtube_candidates(
                song=song,
                candidates=[] if best_candidate is None else (best_candidate.candidates or [best_candidate]),
                winner=None,
            )
            self._playable_cache[cache_key] = fallback_result
            return fallback_result

        self._log_youtube_candidates(song=song, candidates=best_candidate.candidates, winner=best_candidate)
        result = SongResolutionResult(
            song=schemas.SongCreate(
                title=song.title,
                artist=song.artist,
                added_by=song.added_by,
                source="youtube",
                external_url=best_candidate.match.external_url,
            ),
            resolution_confidence=best_candidate.score,
            resolution_reason=", ".join(best_candidate.reasons),
        )
        self._playable_cache[cache_key] = result
        return result

    def _resolve_spotify_playable_song(self, song: schemas.SongCreate) -> SongResolutionResult:
        """Resolve any supported source into a Spotify-backed queue item."""

        if song.source == "spotify" and song.external_url:
            return SongResolutionResult(
                song=song,
                resolution_confidence=1.0,
                resolution_reason="Direct Spotify URL provided.",
            )

        cache_key = self._build_cache_key(song, target="spotify")
        cached_result = self._playable_cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        query = f"track:{song.title} artist:{song.artist}"
        matches = self.spotify_provider.search(query)
        best_match = self._select_best_match(song=song, matches=matches)
        if best_match is None:
            fallback_result = SongResolutionResult(
                song=song,
                resolution_confidence=0.0,
                resolution_reason="No Spotify match found.",
            )
            self._playable_cache[cache_key] = fallback_result
            return fallback_result

        confidence = self._score_match(song=song, match=best_match)
        result = SongResolutionResult(
            song=schemas.SongCreate(
                title=song.title,
                artist=song.artist,
                added_by=song.added_by,
                source="spotify",
                external_url=best_match.external_url,
            ),
            resolution_confidence=confidence,
            resolution_reason="Matched title and artist against Spotify search results.",
        )
        self._playable_cache[cache_key] = result
        return result

    @staticmethod
    def _build_youtube_query(song: schemas.SongCreate) -> str:
        """Build a stable YouTube search query from song metadata."""

        return f"{song.title} {song.artist}"

    @staticmethod
    def _build_cache_key(song: schemas.SongCreate, *, target: str) -> tuple[str, str, str]:
        """Create a deterministic in-memory resolution cache key."""

        return (
            target,
            SongResolverService._normalize_text(song.title),
            SongResolverService._normalize_text(song.artist),
        )

    @staticmethod
    def _select_best_match(
        song: schemas.SongCreate,
        matches: list[ProviderSong],
    ) -> ProviderSong | None:
        """Select the best provider match for a song from search results."""

        scored_matches = [
            (SongResolverService._score_match(song=song, match=match), match)
            for match in matches
        ]
        scored_matches.sort(key=lambda item: item[0], reverse=True)
        return scored_matches[0][1] if scored_matches and scored_matches[0][0] >= 0.35 else None

    def _select_best_youtube_candidate(
        self,
        song: schemas.SongCreate,
        source_metadata: ProviderSong | None,
        matches: list[ProviderSong],
    ) -> ScoredCandidate | None:
        """Evaluate multiple YouTube candidates and choose the most reliable one."""

        candidates = [
            self._score_youtube_candidate(song=song, source_metadata=source_metadata, match=match)
            for match in matches[:10]
        ]
        if not candidates:
            return None

        candidates.sort(key=lambda candidate: candidate.score, reverse=True)
        winner = candidates[0]
        winner.candidates = candidates
        return winner

    @staticmethod
    def _score_match(song: schemas.SongCreate, match: ProviderSong) -> float:
        """Score a provider candidate against the requested song metadata."""

        title_score = SequenceMatcher(
            None,
            SongResolverService._normalize_text(song.title),
            SongResolverService._normalize_text(match.title),
        ).ratio()
        artist_score = SequenceMatcher(
            None,
            SongResolverService._normalize_text(song.artist),
            SongResolverService._normalize_text(match.artist),
        ).ratio()
        provider_score = match.confidence or 0.0
        return max(0.0, min(1.0, (title_score * 0.5) + (artist_score * 0.35) + (provider_score * 0.15)))

    def _score_youtube_candidate(
        self,
        song: schemas.SongCreate,
        source_metadata: ProviderSong | None,
        match: ProviderSong,
    ) -> "ScoredCandidate":
        """Score one YouTube candidate using metadata quality heuristics."""

        normalized_title = self._normalize_text(song.title)
        normalized_artist = self._normalize_text(song.artist)
        candidate_title = self._normalize_text(match.title)
        candidate_artist = self._normalize_text(match.artist)
        channel_title = self._normalize_text(match.channel_title or match.artist)

        score = 0.0
        reasons: list[str] = []

        title_similarity = SequenceMatcher(None, normalized_title, candidate_title).ratio()
        artist_similarity = max(
            SequenceMatcher(None, normalized_artist, candidate_artist).ratio(),
            SequenceMatcher(None, normalized_artist, channel_title).ratio(),
        )

        if match.is_official_artist:
            score += 0.18
            reasons.append("Official artist channel")
        if match.is_official_music_channel:
            score += 0.14
            reasons.append("Official music channel")
        if normalized_title and normalized_title == candidate_title:
            score += 0.2
            reasons.append("Exact title")
        else:
            score += title_similarity * 0.22
            if title_similarity >= 0.88:
                reasons.append("Strong title match")
        if normalized_artist and (normalized_artist == candidate_artist or normalized_artist == channel_title):
            score += 0.2
            reasons.append("Exact artist match")
        else:
            score += artist_similarity * 0.18
            if artist_similarity >= 0.88:
                reasons.append("Strong artist match")

        lowered_title = (match.title or "").lower()
        if "official video" in lowered_title or "official music video" in lowered_title:
            score += 0.12
            reasons.append("Official Video")

        if source_metadata and source_metadata.duration_seconds and match.duration_seconds:
            duration_gap = abs(source_metadata.duration_seconds - match.duration_seconds)
            if duration_gap <= 3:
                score += 0.16
                reasons.append("Exact duration")
            elif duration_gap <= 8:
                score += 0.1
                reasons.append("Close duration")
            elif duration_gap <= 15:
                score += 0.04
            else:
                score -= 0.1
                reasons.append("Duration mismatch")

        for marker in self.NEGATIVE_MARKERS:
            if marker in lowered_title:
                score -= 0.22 if marker in {"live", "cover", "karaoke", "instrumental"} else 0.16
                reasons.append(f"Penalty: {marker}")

        confidence = max(0.0, min(1.0, score))
        if not reasons:
            reasons.append("Weak metadata match")
        return ScoredCandidate(match=match, score=confidence, reasons=reasons)

    def _log_youtube_candidates(
        self,
        song: schemas.SongCreate,
        candidates: list["ScoredCandidate"],
        winner: "ScoredCandidate | None",
    ) -> None:
        """Log scored YouTube candidates and the winning explanation."""

        if not candidates:
            logger.info(
                "YouTube resolution for '%s - %s': no reliable candidate found.",
                song.artist,
                song.title,
            )
            return

        for candidate in candidates:
            logger.info(
                "YouTube candidate '%s' | score=%.2f | reasons=%s",
                candidate.match.title,
                candidate.score,
                "; ".join(candidate.reasons),
            )

        if winner is None:
            logger.info(
                "YouTube resolution for '%s - %s': no reliable match.",
                song.artist,
                song.title,
            )
            return

        logger.info(
            "YouTube winner '%s' | score=%.2f | reasons=%s",
            winner.match.title,
            winner.score,
            "; ".join(winner.reasons),
        )

    @staticmethod
    def _normalize_text(value: str) -> str:
        """Normalize text for deterministic similarity checks."""

        lowered = value.strip().lower()
        lowered = re.sub(r"\([^)]*\)", " ", lowered)
        lowered = re.sub(r"[^a-z0-9]+", " ", lowered)
        return " ".join(lowered.split())


@dataclass(slots=True)
class ScoredCandidate:
    """Scored YouTube candidate with human-readable reasoning."""

    match: ProviderSong
    score: float
    reasons: list[str]
    candidates: list["ScoredCandidate"] | None = None
