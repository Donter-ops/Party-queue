from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProviderMatch:
    """Planned playback mapping for one canonical song.

    The playback engine consumes this model instead of raw queue songs so
    future playback adapters can receive a normalized provider target and track
    identifier without re-implementing matching logic.
    """

    provider: str | None
    provider_track_id: str | None
    confidence: float
    fallback_provider: str | None = None
    resolved_title: str | None = None
    resolved_artist: str | None = None
