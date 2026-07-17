from __future__ import annotations

from playback.playback_engine import PlaybackEngine, PlaybackSession
from providers.youtube_playback import YouTubePlaybackProvider
from services.queue_service import QueueService

import schemas


class PlaybackService:
    """Application service for room playback workflows.

    Routes use this service instead of calling the playback engine directly.
    The service preserves the existing provider-independent engine while
    shaping its in-memory session state into a stable API contract for the web
    player layer.
    """

    def __init__(
        self,
        playback_engine: PlaybackEngine,
        queue_service: QueueService,
        youtube_playback_provider: YouTubePlaybackProvider,
    ) -> None:
        self.playback_engine = playback_engine
        self.queue_service = queue_service
        self.youtube_playback_provider = youtube_playback_provider

    def get_session(self, room_id: str) -> schemas.PlaybackSessionResponse | None:
        """Return the current playback session for a room when present."""

        self.queue_service.require_room(room_id)
        session = self.playback_engine.get_session(room_id)
        if session is None:
            return None
        return self._to_response(session)

    def start(self, room_id: str) -> schemas.PlaybackSessionResponse:
        """Start playback for a room queue."""

        return self._to_response(self.playback_engine.start(room_id))

    def pause(self, room_id: str) -> schemas.PlaybackSessionResponse:
        """Pause the active playback session."""

        return self._to_response(self.playback_engine.pause(room_id))

    def resume(self, room_id: str) -> schemas.PlaybackSessionResponse:
        """Resume playback for a room."""

        return self._to_response(self.playback_engine.resume(room_id))

    def finish(self, room_id: str) -> schemas.PlaybackSessionResponse:
        """Mark the active item as finished and advance playback."""

        return self._to_response(self.playback_engine.finish(room_id))

    def next(self, room_id: str) -> schemas.PlaybackSessionResponse:
        """Advance playback without requiring a terminal state first."""

        return self._to_response(self.playback_engine.next(room_id))

    def _to_response(self, session: PlaybackSession) -> schemas.PlaybackSessionResponse:
        """Convert the in-memory engine session into an API response."""

        next_song = self.queue_service.get_next_song(
            room_id=session.room_id,
            current_position=session.queue_position,
        )
        youtube_video_id = None
        if session.provider_match and session.provider_match.provider == "youtube_music":
            youtube_video_id = self.youtube_playback_provider.resolve_video_id(
                provider_track_id=session.provider_match.provider_track_id,
                external_url=session.current_song.external_url if session.current_song else None,
            )

        provider_match = None
        if session.provider_match is not None:
            provider_match = schemas.PlaybackProviderMatchResponse(
                provider=session.provider_match.provider,
                provider_track_id=session.provider_match.provider_track_id,
                confidence=session.provider_match.confidence,
                fallback_provider=session.provider_match.fallback_provider,
                resolved_title=session.provider_match.resolved_title,
                resolved_artist=session.provider_match.resolved_artist,
            )

        return schemas.PlaybackSessionResponse(
            room_id=session.room_id,
            current_song=(
                schemas.SongResponse.model_validate(session.current_song)
                if session.current_song is not None
                else None
            ),
            next_song=(
                schemas.SongResponse.model_validate(next_song)
                if next_song is not None
                else None
            ),
            provider_match=provider_match,
            youtube_video_id=youtube_video_id,
            queue_position=session.queue_position,
            state=session.state,
            started_at=session.started_at,
            updated_at=session.updated_at,
        )
