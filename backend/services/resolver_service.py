from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
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


@dataclass(slots=True)
class ScoreContribution:
    """One score delta emitted by the deterministic YouTube resolver."""

    label: str
    value: float
    kind: str
    detail: str


@dataclass(slots=True)
class ScoredCandidate:
    """Scored YouTube candidate with human-readable reasoning."""

    match: ProviderSong
    score: float
    reasons: list[str]
    contributions: list[ScoreContribution]
    rank: int = 0
    candidates: list["ScoredCandidate"] | None = None


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
        self._debug_trace_cache: dict[tuple[str, str, str], schemas.ResolverDebugTrace] = {}
        self._latest_trace: schemas.ResolverDebugTrace | None = None

    def resolve_song(self, song: schemas.SongCreate) -> schemas.SongCreate:
        """Delegate song preparation to the orchestrator agent."""

        return self.resolve_song_for_queue(song).song

    def resolve_song_for_queue(self, song: schemas.SongCreate) -> SongResolutionResult:
        """Resolve a queue item into the host's playable provider when possible."""

        _decision = self.decide_song(song)
        normalized_song, source_metadata = self._normalize_source_song(song)
        return self._resolve_host_playable_song(normalized_song, source_metadata)

    def decide_song(self, song: schemas.SongCreate) -> AgentDecision:
        """Return the structured orchestration decision for the incoming song."""

        return self.orchestrator_agent.decide(song)

    def get_latest_trace(self) -> schemas.ResolverDebugTrace | None:
        """Return the latest resolver trace captured in the current request."""

        return self._latest_trace

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
        self._latest_trace = None
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
        cached_trace = self._debug_trace_cache.get(cache_key)
        if cached_result is not None:
            if cached_trace is not None:
                self._latest_trace = cached_trace.model_copy(
                    deep=True,
                    update={"created_at": self._now(), "cache_hit": True},
                )
            return SongResolutionResult(
                song=cached_result.song,
                resolution_confidence=cached_result.resolution_confidence,
                resolution_reason=(
                    f"Cached: {cached_result.resolution_reason}"
                    if cached_result.resolution_reason
                    else "Cached"
                ),
            )

        search_query = self._build_youtube_query(song)
        self._trace_spotify_resolution_input(source_metadata=source_metadata, search_query=search_query)
        matches = self.youtube_provider.search(search_query)
        best_candidate = self._select_best_youtube_candidate(
            song=song,
            source_metadata=source_metadata,
            matches=matches,
        )

        if best_candidate is None or best_candidate.score < self.YOUTUBE_CONFIDENCE_THRESHOLD:
            candidates = [] if best_candidate is None else (best_candidate.candidates or [best_candidate])
            trace = self._build_debug_trace(
                song=song,
                source_metadata=source_metadata,
                search_query=search_query,
                candidates=candidates,
                winner=None,
                cache_hit=False,
                reason="No reliable match",
            )
            self._latest_trace = trace
            fallback_result = SongResolutionResult(
                song=song,
                resolution_confidence=0.0,
                resolution_reason="No reliable match",
            )
            self._log_youtube_candidates(song=song, candidates=candidates, winner=None)
            self._playable_cache[cache_key] = fallback_result
            self._debug_trace_cache[cache_key] = trace
            return fallback_result

        trace = self._build_debug_trace(
            song=song,
            source_metadata=source_metadata,
            search_query=search_query,
            candidates=best_candidate.candidates or [best_candidate],
            winner=best_candidate,
            cache_hit=False,
            reason=", ".join(best_candidate.reasons),
        )
        self._latest_trace = trace
        self._log_youtube_candidates(
            song=song,
            candidates=best_candidate.candidates or [best_candidate],
            winner=best_candidate,
        )

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
        self._debug_trace_cache[cache_key] = trace
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
            return SongResolutionResult(
                song=cached_result.song,
                resolution_confidence=cached_result.resolution_confidence,
                resolution_reason=(
                    f"Cached: {cached_result.resolution_reason}"
                    if cached_result.resolution_reason
                    else "Cached"
                ),
            )

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
        for index, candidate in enumerate(candidates, start=1):
            candidate.rank = index
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
    ) -> ScoredCandidate:
        """Score one YouTube candidate using metadata quality heuristics."""

        normalized_title = self._normalize_text(song.title)
        normalized_artist = self._normalize_text(song.artist)
        candidate_title = self._normalize_text(match.title)
        candidate_artist = self._normalize_text(match.artist)
        channel_title = self._normalize_text(match.channel_title or match.artist)

        score = 0.0
        reasons: list[str] = []
        contributions: list[ScoreContribution] = []

        title_similarity = SequenceMatcher(None, normalized_title, candidate_title).ratio()
        artist_similarity = max(
            SequenceMatcher(None, normalized_artist, candidate_artist).ratio(),
            SequenceMatcher(None, normalized_artist, channel_title).ratio(),
        )

        if match.is_official_artist:
            score += 0.18
            reasons.append("Official artist channel")
            contributions.append(
                ScoreContribution(
                    label="Official artist channel",
                    value=0.18,
                    kind="positive",
                    detail="Channel metadata matched the official-artist heuristic.",
                )
            )
        if match.is_official_music_channel:
            score += 0.14
            reasons.append("Official music channel")
            contributions.append(
                ScoreContribution(
                    label="Official music channel",
                    value=0.14,
                    kind="positive",
                    detail="Channel metadata matched the music-channel heuristic.",
                )
            )
        if normalized_title and normalized_title == candidate_title:
            score += 0.2
            reasons.append("Exact title")
            contributions.append(
                ScoreContribution(
                    label="Exact title",
                    value=0.2,
                    kind="positive",
                    detail="Normalized Spotify title exactly matched the candidate title.",
                )
            )
        else:
            title_contribution = title_similarity * 0.22
            score += title_contribution
            contributions.append(
                ScoreContribution(
                    label="Title similarity",
                    value=title_contribution,
                    kind="positive",
                    detail=f"Sequence similarity: {title_similarity:.2f}.",
                )
            )
            if title_similarity >= 0.88:
                reasons.append("Strong title match")
        if normalized_artist and (normalized_artist == candidate_artist or normalized_artist == channel_title):
            score += 0.2
            reasons.append("Exact artist match")
            contributions.append(
                ScoreContribution(
                    label="Exact artist match",
                    value=0.2,
                    kind="positive",
                    detail="Normalized Spotify artist exactly matched the candidate artist or channel.",
                )
            )
        else:
            artist_contribution = artist_similarity * 0.18
            score += artist_contribution
            contributions.append(
                ScoreContribution(
                    label="Artist similarity",
                    value=artist_contribution,
                    kind="positive",
                    detail=f"Best artist similarity: {artist_similarity:.2f}.",
                )
            )
            if artist_similarity >= 0.88:
                reasons.append("Strong artist match")

        lowered_title = (match.title or "").lower()
        if "official video" in lowered_title or "official music video" in lowered_title:
            score += 0.12
            reasons.append("Official Video")
            contributions.append(
                ScoreContribution(
                    label="Official video keyword",
                    value=0.12,
                    kind="positive",
                    detail="Video title contains an official-video marker.",
                )
            )

        if source_metadata and source_metadata.duration_seconds and match.duration_seconds:
            duration_gap = abs(source_metadata.duration_seconds - match.duration_seconds)
            if duration_gap <= 3:
                score += 0.16
                reasons.append("Exact duration")
                contributions.append(
                    ScoreContribution(
                        label="Duration match",
                        value=0.16,
                        kind="positive",
                        detail=f"Duration gap {duration_gap}s.",
                    )
                )
            elif duration_gap <= 8:
                score += 0.1
                reasons.append("Close duration")
                contributions.append(
                    ScoreContribution(
                        label="Duration match",
                        value=0.1,
                        kind="positive",
                        detail=f"Duration gap {duration_gap}s.",
                    )
                )
            elif duration_gap <= 15:
                score += 0.04
                contributions.append(
                    ScoreContribution(
                        label="Duration match",
                        value=0.04,
                        kind="positive",
                        detail=f"Duration gap {duration_gap}s.",
                    )
                )
            else:
                score -= 0.1
                reasons.append("Duration mismatch")
                contributions.append(
                    ScoreContribution(
                        label="Duration mismatch",
                        value=-0.1,
                        kind="negative",
                        detail=f"Duration gap {duration_gap}s.",
                    )
                )

        for marker in self.NEGATIVE_MARKERS:
            if marker in lowered_title:
                penalty = 0.22 if marker in {"live", "cover", "karaoke", "instrumental"} else 0.16
                score -= penalty
                reasons.append(f"Penalty: {marker}")
                contributions.append(
                    ScoreContribution(
                        label=f"Penalty: {marker}",
                        value=-penalty,
                        kind="negative",
                        detail="Negative title marker detected.",
                    )
                )

        confidence = max(0.0, min(1.0, score))
        if not reasons:
            reasons.append("Weak metadata match")
        return ScoredCandidate(
            match=match,
            score=confidence,
            reasons=reasons,
            contributions=contributions,
        )

    def _build_debug_trace(
        self,
        song: schemas.SongCreate,
        source_metadata: ProviderSong | None,
        search_query: str,
        candidates: list[ScoredCandidate],
        winner: ScoredCandidate | None,
        cache_hit: bool,
        reason: str,
    ) -> schemas.ResolverDebugTrace:
        """Create a complete development trace for one YouTube resolution."""

        winner_score = winner.score if winner is not None else 0.0
        winner_rank = winner.rank if winner is not None else None
        spotify = None
        if source_metadata is not None and source_metadata.provider == "spotify":
            spotify = schemas.ResolverSpotifyMetadata(
                track_id=source_metadata.provider_id or None,
                track_name=source_metadata.title,
                artists=list(source_metadata.artists or [source_metadata.artist]),
                album=source_metadata.album,
                duration_ms=source_metadata.duration_ms,
                isrc=source_metadata.isrc,
            )
        elif song.source == "spotify":
            spotify = schemas.ResolverSpotifyMetadata(
                track_id=None,
                track_name=song.title,
                artists=[artist.strip() for artist in song.artist.split(",") if artist.strip()],
                album=None,
                duration_ms=None,
                isrc=None,
            )

        return schemas.ResolverDebugTrace(
            created_at=self._now(),
            source_provider=song.source,
            target_provider="youtube_music",
            cache_hit=cache_hit,
            spotify=spotify,
            search_query=search_query,
            candidates=[
                schemas.ResolverCandidateTrace(
                    rank=candidate.rank,
                    video_id=candidate.match.provider_id,
                    video_title=candidate.match.title,
                    channel=candidate.match.channel_title or candidate.match.artist,
                    duration_seconds=candidate.match.duration_seconds,
                    score=candidate.score,
                    confidence=candidate.score,
                    contributions=[
                        schemas.ResolverScoreContribution(
                            label=contribution.label,
                            value=contribution.value,
                            kind=contribution.kind,
                            detail=contribution.detail,
                        )
                        for contribution in candidate.contributions
                    ],
                    reasons=list(candidate.reasons),
                    lost_reason=(
                        None
                        if winner is not None and candidate.match.provider_id == winner.match.provider_id
                        else self._describe_candidate_loss(
                            candidate=candidate,
                            winning_score=winner_score,
                            winning_rank=winner_rank,
                        )
                    ),
                )
                for candidate in candidates
            ],
            winner=schemas.ResolverWinnerTrace(
                video_id=winner.match.provider_id if winner is not None else None,
                video_title=winner.match.title if winner is not None else None,
                confidence=winner_score,
                reason=reason,
            ),
            confidence=winner_score,
            reason=reason,
        )

    @staticmethod
    def _describe_candidate_loss(
        candidate: ScoredCandidate,
        winning_score: float,
        winning_rank: int | None,
    ) -> str:
        """Explain why a candidate lost to the current winner."""

        if winning_rank is None:
            return "No winner selected."
        delta = max(0.0, winning_score - candidate.score)
        negative_labels = ", ".join(
            contribution.label for contribution in candidate.contributions if contribution.value < 0
        )
        if negative_labels:
            return f"Scored {delta:.2f} below the winner because of lower-ranked signals: {negative_labels}."
        if delta > 0:
            return f"Scored {delta:.2f} below the winner and ranked #{candidate.rank}."
        return f"Ranked below the winner at position {candidate.rank}."

    def _log_youtube_candidates(
        self,
        song: schemas.SongCreate,
        candidates: list[ScoredCandidate],
        winner: ScoredCandidate | None,
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
                (
                    "YouTube candidate | video_id=%s | title=%s | channel=%s | duration_seconds=%s "
                    "| score=%.2f | confidence=%.2f | contributions=%s | reasons=%s"
                ),
                candidate.match.provider_id,
                candidate.match.title,
                candidate.match.channel_title or candidate.match.artist,
                candidate.match.duration_seconds,
                candidate.score,
                candidate.score,
                "; ".join(
                    f"{contribution.label}={contribution.value:+.2f}"
                    for contribution in candidate.contributions
                ),
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
            "YouTube winner | video_id=%s | title=%s | score=%.2f | reasons=%s",
            winner.match.provider_id,
            winner.match.title,
            winner.score,
            "; ".join(winner.reasons),
        )

        for candidate in candidates:
            if candidate.match.provider_id == winner.match.provider_id:
                continue
            logger.info(
                "YouTube loser | video_id=%s | lost_reason=%s",
                candidate.match.provider_id,
                self._describe_candidate_loss(
                    candidate=candidate,
                    winning_score=winner.score,
                    winning_rank=winner.rank,
                ),
            )

    def _trace_spotify_resolution_input(
        self,
        source_metadata: ProviderSong | None,
        search_query: str,
    ) -> None:
        """Log the Spotify source metadata before YouTube matching begins."""

        if source_metadata is None or source_metadata.provider != "spotify":
            return
        logger.info(
            (
                "Spotify resolution input | track_id=%s | track_name=%s | artists=%s | "
                "album=%s | duration_ms=%s | isrc=%s | youtube_query=%s"
            ),
            source_metadata.provider_id,
            source_metadata.title,
            ", ".join(source_metadata.artists or [source_metadata.artist]),
            source_metadata.album,
            source_metadata.duration_ms,
            source_metadata.isrc,
            search_query,
        )

    @staticmethod
    def _normalize_text(value: str) -> str:
        """Normalize text for deterministic similarity checks."""

        lowered = value.strip().lower()
        lowered = re.sub(r"\([^)]*\)", " ", lowered)
        lowered = re.sub(r"[^a-z0-9]+", " ", lowered)
        return " ".join(lowered.split())

    @staticmethod
    def _now() -> datetime:
        """Return the current UTC timestamp for trace capture."""

        return datetime.now(UTC)
