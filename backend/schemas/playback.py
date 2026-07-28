from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from playback.playback_state import PlaybackState
from schemas.song import SongResponse


class PlaybackProviderMatchResponse(BaseModel):
    """Serialized provider match returned to the web player layer."""

    provider: str | None
    provider_track_id: str | None
    confidence: float
    fallback_provider: str | None = None
    resolved_title: str | None = None
    resolved_artist: str | None = None


class PlaybackSessionResponse(BaseModel):
    """Provider-independent playback session payload for the frontend.

    The response exposes only the data the web application needs to render the
    current transport state, choose a player surface, and move to the next
    queue entry when playback completes.
    """

    room_id: str
    current_song: SongResponse | None
    next_song: SongResponse | None
    provider_match: PlaybackProviderMatchResponse | None
    youtube_video_id: str | None = None
    queue_position: int | None
    previous_available: bool = False
    queue_length: int = 0
    current_provider: str | None = None
    playable_provider: str | None = None
    current_song_id: str | None = None
    resolver_cache_hit: bool = False
    state: PlaybackState
    started_at: datetime | None
    updated_at: datetime
