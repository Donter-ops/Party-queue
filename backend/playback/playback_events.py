from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC
from enum import StrEnum
from typing import Any

import models

from playback.playback_state import PlaybackState


class PlaybackEventType(StrEnum):
    """Typed event names emitted by the playback engine.

    The event layer provides a durable extension point for future provider
    adapters, analytics, websockets, and automation workflows. The current
    implementation keeps events in memory, but the shape is stable enough to be
    forwarded elsewhere later without redesigning PlaybackEngine.
    """

    STARTED = "STARTED"
    PAUSED = "PAUSED"
    RESUMED = "RESUMED"
    FINISHED = "FINISHED"
    SKIPPED = "SKIPPED"
    ADVANCED = "ADVANCED"
    IDLED = "IDLED"


@dataclass(slots=True)
class PlaybackEvent:
    """Structured description of one playback transition.

    Every state change is captured as an event so the engine can mark songs as
    finished or skipped without modifying the persistence layer. This keeps the
    queue schema stable while still producing explicit playback history.
    """

    room_id: str
    event_type: PlaybackEventType
    state: PlaybackState
    song: models.Song | None = None
    occurred_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    metadata: dict[str, Any] = field(default_factory=dict)
