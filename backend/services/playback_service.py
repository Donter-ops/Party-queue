from __future__ import annotations

from datetime import datetime

import models
from playback.playback_events import PlaybackEventType
from playback.playback_engine import PlaybackEngine, PlaybackSession
from playback.playback_state import PlaybackState
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

    _history: dict[str, list[str]] = {}

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

        self._remember_current_song(room_id)
        return self._to_response(self.playback_engine.finish(room_id))

    def next(self, room_id: str) -> schemas.PlaybackSessionResponse:
        """Finish the current item and advance playback to the next song."""

        session = self.playback_engine.get_session(room_id)
        if session is None or session.current_song is None:
            return self._to_response(self.playback_engine.start(room_id))
        self._remember_current_song(room_id)
        return self._to_response(self.playback_engine.finish(room_id))

    def previous(self, room_id: str) -> schemas.PlaybackSessionResponse:
        """Restore the previous playable song from in-memory room history."""

        self.queue_service.require_room(room_id)
        history = self._history.get(room_id, [])
        current_session = self.playback_engine.get_session(room_id)

        while history:
            previous_song_id = history.pop()
            previous_song = self.queue_service.get_song(room_id=room_id, song_id=previous_song_id)
            if previous_song is None:
                continue

            if current_session and current_session.current_song is not None:
                self._append_history_entry(room_id, current_session.current_song.id)

            return self._to_response(
                self._build_playing_session(
                    room_id=room_id,
                    song=previous_song,
                    started_at=(current_session.started_at if current_session else None),
                    events=list(current_session.events) if current_session else [],
                    event_type=PlaybackEventType.ADVANCED,
                )
            )

        return self.get_session(room_id) or self._to_response(self.playback_engine.start(room_id))

    def handle_deleted_song(self, room_id: str, song_id: str, deleted_position: int) -> None:
        """Keep playback state consistent when a queue item is removed."""

        self._history[room_id] = [
            previous_song_id
            for previous_song_id in self._history.get(room_id, [])
            if previous_song_id != song_id
        ]

        session = self.playback_engine.get_session(room_id)
        if session is None or session.current_song is None or session.current_song.id != song_id:
            return

        remaining_songs = self.queue_service.list_songs(room_id)
        next_song = next(
            (song for song in remaining_songs if song.position >= deleted_position),
            None,
        )
        if next_song is None and remaining_songs:
            next_song = remaining_songs[0]

        if next_song is None:
            idle_session = PlaybackSession(
                room_id=room_id,
                current_song=None,
                provider_match=None,
                queue_position=None,
                state=PlaybackState.IDLE,
                started_at=session.started_at,
                updated_at=self._now(),
                events=list(session.events),
            )
            self.playback_engine._append_event(idle_session, PlaybackEventType.IDLED, PlaybackState.IDLE)
            self.playback_engine._store_session(idle_session)
            return

        self.playback_engine._store_session(
            self._build_playing_session(
                room_id=room_id,
                song=next_song,
                started_at=session.started_at,
                events=list(session.events),
                event_type=PlaybackEventType.ADVANCED,
            )
        )

    def _to_response(self, session: PlaybackSession) -> schemas.PlaybackSessionResponse:
        """Convert the in-memory engine session into an API response."""

        songs = self.queue_service.list_songs(session.room_id)
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

        current_song = (
            schemas.SongResponse.model_validate(session.current_song)
            if session.current_song is not None
            else None
        )
        current_provider = session.current_song.source if session.current_song is not None else None
        resolution_reason = session.current_song.resolution_reason if session.current_song is not None else None

        return schemas.PlaybackSessionResponse(
            room_id=session.room_id,
            current_song=current_song,
            next_song=(
                schemas.SongResponse.model_validate(next_song)
                if next_song is not None
                else None
            ),
            provider_match=provider_match,
            youtube_video_id=youtube_video_id,
            queue_position=session.queue_position,
            previous_available=bool(self._history.get(session.room_id)),
            queue_length=len(songs),
            current_provider=current_provider,
            playable_provider=session.provider_match.provider if session.provider_match is not None else None,
            current_song_id=session.current_song.id if session.current_song is not None else None,
            resolver_cache_hit=bool(resolution_reason and resolution_reason.lower().startswith("cached")),
            state=session.state,
            started_at=session.started_at,
            updated_at=session.updated_at,
        )

    def _remember_current_song(self, room_id: str) -> None:
        """Store the currently playing song in room history before advancing."""

        session = self.playback_engine.get_session(room_id)
        if session is None or session.current_song is None:
            return
        self._append_history_entry(room_id, session.current_song.id)

    def _append_history_entry(self, room_id: str, song_id: str) -> None:
        """Append one song identifier to room history without duplicates in a row."""

        history = self._history.setdefault(room_id, [])
        if history and history[-1] == song_id:
            return
        history.append(song_id)

    def _build_playing_session(
        self,
        room_id: str,
        song: models.Song,
        started_at: datetime | None,
        events: list,
        event_type: PlaybackEventType,
    ) -> PlaybackSession:
        """Create and persist a new active session for a concrete queue song."""

        session = PlaybackSession(
            room_id=room_id,
            current_song=song,
            provider_match=self.playback_engine._build_provider_match(song),
            queue_position=song.position,
            state=PlaybackState.PLAYING,
            started_at=started_at or self._now(),
            updated_at=self._now(),
            events=events,
        )
        self.playback_engine._start_provider_playback(session.provider_match)
        self.playback_engine._append_event(session, event_type, PlaybackState.PLAYING)
        return session

    @staticmethod
    def _now() -> datetime:
        """Return the current UTC timestamp for service-level session updates."""

        return PlaybackEngine._now()
