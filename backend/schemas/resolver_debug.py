from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class ResolverScoreContribution(BaseModel):
    """One deterministic score contribution for a YouTube candidate.

    The resolver debug view needs to explain exactly how a candidate's final
    score was assembled. Each contribution records the rule name, whether it
    helped or hurt, and the numeric delta applied by the current heuristic.
    """

    label: str
    value: float
    kind: str
    detail: str


class ResolverSpotifyMetadata(BaseModel):
    """Spotify metadata captured before cross-provider matching starts."""

    track_id: str | None = None
    track_name: str
    artists: list[str] = Field(default_factory=list)
    album: str | None = None
    duration_ms: int | None = None
    isrc: str | None = None


class ResolverCandidateTrace(BaseModel):
    """Trace entry for one returned YouTube candidate."""

    rank: int
    video_id: str
    video_title: str
    channel: str | None = None
    duration_seconds: int | None = None
    score: float
    confidence: float
    contributions: list[ResolverScoreContribution] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    lost_reason: str | None = None


class ResolverWinnerTrace(BaseModel):
    """Summary of the winning YouTube candidate."""

    video_id: str | None = None
    video_title: str | None = None
    confidence: float
    reason: str


class ResolverDebugTrace(BaseModel):
    """Complete resolution trace for one room-scoped song resolution.

    The trace is intentionally verbose and development-only. It captures the
    input metadata, generated search query, scored candidates, final winner,
    and explanatory text so mismatches can be inspected before the scoring
    algorithm itself is changed.
    """

    created_at: datetime
    room_id: str | None = None
    source_provider: str
    target_provider: str
    cache_hit: bool = False
    spotify: ResolverSpotifyMetadata | None = None
    search_query: str | None = None
    candidates: list[ResolverCandidateTrace] = Field(default_factory=list)
    winner: ResolverWinnerTrace
    confidence: float
    reason: str
