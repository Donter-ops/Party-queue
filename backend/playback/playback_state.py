from __future__ import annotations

from enum import StrEnum


class PlaybackState(StrEnum):
    """Lifecycle states for a room-scoped playback session.

    The enum is intentionally provider-agnostic. It describes only the local
    orchestration state maintained by PartyQueue, so future Spotify, YouTube,
    or hardware playback connectors can map their own transport semantics onto
    this stable internal contract.
    """

    IDLE = "IDLE"
    PLAYING = "PLAYING"
    PAUSED = "PAUSED"
    FINISHED = "FINISHED"
    SKIPPED = "SKIPPED"
