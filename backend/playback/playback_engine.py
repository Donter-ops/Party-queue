from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, UTC

import models
from auth.spotify_playback_client import SpotifyPlaybackClient, SpotifyPlaybackError
from services.queue_service import QueueService
from services.input_resolver import CanonicalSong

from playback.playback_events import PlaybackEvent, PlaybackEventType
from playback.host_provider import HostCapabilities
from playback.playback_resolver import PlaybackResolver
from playback.provider_match import ProviderMatch
from playback.playback_state import PlaybackState


@dataclass(slots=True)
class PlaybackSession:
    """In-memory playback snapshot for one room.

    The session describes which song is currently active, where playback is in
    the queue, and which transport state the room is in. The model is kept
    separate from SQLAlchemy persistence on purpose so provider-specific
    playback backends can be introduced later without forcing queue schema
    changes or endpoint migrations.
    """

    room_id: str
    current_song: models.Song | None
    provider_match: ProviderMatch | None
    queue_position: int | None
    state: PlaybackState
    started_at: datetime | None
    updated_at: datetime
    events: list[PlaybackEvent] = field(default_factory=list)


class PlaybackEngine:
    """Stateful playback coordinator built on top of QueueService.

    The engine owns playback state transitions and delegates provider-specific
    execution only after the existing playback resolver has produced a concrete
    ProviderMatch. QueueService remains the source of truth for ordering, and
    public API contracts remain unchanged while real provider playback is
    introduced behind the existing backend service boundary.
    """

    _sessions: dict[str, PlaybackSession] = {}

    def __init__(
        self,
        queue_service: QueueService,
        playback_resolver: PlaybackResolver,
        host_capabilities: HostCapabilities,
        spotify_playback_client: SpotifyPlaybackClient,
    ) -> None:
        self.queue_service = queue_service
        self.playback_resolver = playback_resolver
        self.host_capabilities = host_capabilities
        self.spotify_playback_client = spotify_playback_client

    def start(self, room_id: str) -> PlaybackSession:
        """Start playback from the current room queue head.

        If the room has queued songs, playback enters the PLAYING state on the
        first song. If the queue is empty, the room remains IDLE.
        """

        self.queue_service.require_room(room_id)
        songs = self.queue_service.list_songs(room_id)
        current_time = self._now()

        if not songs:
            session = self._build_idle_session(room_id=room_id, updated_at=current_time)
            self._append_event(session, PlaybackEventType.IDLED, PlaybackState.IDLE)
            return self._store_session(session)

        current_song = songs[0]
        session = PlaybackSession(
            room_id=room_id,
            current_song=current_song,
            provider_match=self._build_provider_match(current_song),
            queue_position=current_song.position,
            state=PlaybackState.PLAYING,
            started_at=current_time,
            updated_at=current_time,
        )
        self._start_provider_playback(session.provider_match)
        self._append_event(session, PlaybackEventType.STARTED, PlaybackState.PLAYING)
        return self._store_session(session)

    def pause(self, room_id: str) -> PlaybackSession:
        """Pause the active playback session for a room."""

        session = self._require_session(room_id)
        session.state = PlaybackState.PAUSED if session.provider_match else PlaybackState.IDLE
        session.updated_at = self._now()
        self._append_event(session, PlaybackEventType.PAUSED, session.state)
        return self._store_session(session)

    def resume(self, room_id: str) -> PlaybackSession:
        """Resume a paused room or start playback if no session exists yet."""

        session = self._get_session(room_id)
        if session is None:
            return self.start(room_id)

        if session.provider_match is None:
            return self.start(room_id)

        session.state = PlaybackState.PLAYING
        session.updated_at = self._now()
        if session.started_at is None:
            session.started_at = session.updated_at
        self._start_provider_playback(session.provider_match)
        self._append_event(session, PlaybackEventType.RESUMED, PlaybackState.PLAYING)
        return self._store_session(session)

    def finish(self, room_id: str) -> PlaybackSession:
        """Mark the current song as finished and advance automatically.

        The completed song is recorded through an in-memory playback event. The
        queue itself remains unchanged. After recording the completion, the
        engine advances to the next queued song or falls back to IDLE when the
        queue is exhausted.
        """

        session = self._require_session(room_id)
        session.updated_at = self._now()
        session.state = PlaybackState.FINISHED
        self._append_event(session, PlaybackEventType.FINISHED, PlaybackState.FINISHED)
        return self._advance(room_id=room_id, current_session=session, event_type=PlaybackEventType.ADVANCED)

    def skip(self, room_id: str) -> PlaybackSession:
        """Skip the current song and advance to the next queue entry."""

        session = self._require_session(room_id)
        session.updated_at = self._now()
        session.state = PlaybackState.SKIPPED
        self._append_event(session, PlaybackEventType.SKIPPED, PlaybackState.SKIPPED)
        return self._advance(room_id=room_id, current_session=session, event_type=PlaybackEventType.ADVANCED)

    def next(self, room_id: str) -> PlaybackSession:
        """Advance to the next queue entry without marking a terminal state."""

        session = self._get_session(room_id)
        if session is None:
            return self.start(room_id)

        session.updated_at = self._now()
        return self._advance(room_id=room_id, current_session=session, event_type=PlaybackEventType.ADVANCED)

    def get_session(self, room_id: str) -> PlaybackSession | None:
        """Return the current in-memory playback session for a room."""

        return self._sessions.get(room_id)

    def _advance(
        self,
        room_id: str,
        current_session: PlaybackSession,
        event_type: PlaybackEventType,
    ) -> PlaybackSession:
        """Move playback to the next song or transition the room to IDLE."""

        next_song = self.queue_service.get_next_song(
            room_id=room_id,
            current_position=current_session.queue_position,
        )
        current_time = self._now()

        if next_song is None:
            idle_session = PlaybackSession(
                room_id=room_id,
                current_song=None,
                provider_match=None,
                queue_position=None,
                state=PlaybackState.IDLE,
                started_at=current_session.started_at,
                updated_at=current_time,
                events=list(current_session.events),
            )
            self._append_event(idle_session, PlaybackEventType.IDLED, PlaybackState.IDLE)
            return self._store_session(idle_session)

        next_session = PlaybackSession(
            room_id=room_id,
            current_song=next_song,
            provider_match=self._build_provider_match(next_song),
            queue_position=next_song.position,
            state=PlaybackState.PLAYING,
            started_at=current_session.started_at or current_time,
            updated_at=current_time,
            events=list(current_session.events),
        )
        self._start_provider_playback(next_session.provider_match)
        self._append_event(next_session, event_type, PlaybackState.PLAYING)
        return self._store_session(next_session)

    def _build_idle_session(self, room_id: str, updated_at: datetime) -> PlaybackSession:
        """Construct an empty session for rooms without queued songs."""

        return PlaybackSession(
            room_id=room_id,
            current_song=None,
            provider_match=None,
            queue_position=None,
            state=PlaybackState.IDLE,
            started_at=None,
            updated_at=updated_at,
        )

    def _append_event(
        self,
        session: PlaybackSession,
        event_type: PlaybackEventType,
        state: PlaybackState,
    ) -> None:
        """Attach a structured event to the session history."""

        session.events.append(
            PlaybackEvent(
                room_id=session.room_id,
                event_type=event_type,
                state=state,
                song=session.current_song,
                provider_match=session.provider_match,
                metadata={
                    "queue_position": session.queue_position,
                    "provider": session.provider_match.provider if session.provider_match else None,
                    "provider_track_id": (
                        session.provider_match.provider_track_id
                        if session.provider_match
                        else None
                    ),
                },
            )
        )

    def _build_provider_match(self, song: models.Song) -> ProviderMatch:
        """Convert a queue song into a provider-independent playback plan."""

        canonical_song = CanonicalSong(
            title=song.title,
            artist=song.artist,
            provider=song.source,
            confidence=1.0,
            external_id=song.external_url or song.id,
            external_url=song.external_url,
        )
        return self.playback_resolver.resolve(canonical_song, self.host_capabilities)

    def _start_provider_playback(self, provider_match: ProviderMatch | None) -> None:
        """Dispatch resolved playback to the currently supported host provider.

        The engine keeps provider selection inside the existing playback
        resolver flow. Only the final provider-specific execution happens here,
        which lets PartyQueue start real playback without changing queue, API,
        or orchestration contracts.
        """

        if provider_match is None or provider_match.provider != "spotify":
            return
        if not provider_match.provider_track_id:
            raise SpotifyPlaybackError("Spotify playback could not start because no track ID was resolved.")

        devices = self.spotify_playback_client.get_available_devices()
        active_device = next((device for device in devices if device.is_active), None)
        if active_device is None:
            raise SpotifyPlaybackError("No active Spotify device found.")

        self.spotify_playback_client.play_track(
            device_id=active_device.device_id,
            spotify_track_id=provider_match.provider_track_id,
        )

    def _get_session(self, room_id: str) -> PlaybackSession | None:
        """Return a session when present without creating one implicitly."""

        return self._sessions.get(room_id)

    def _require_session(self, room_id: str) -> PlaybackSession:
        """Return an existing session or create one from the queue state."""

        session = self._get_session(room_id)
        if session is not None:
            return session
        return self.start(room_id)

    def _store_session(self, session: PlaybackSession) -> PlaybackSession:
        """Persist the in-memory session snapshot for future playback calls."""

        self._sessions[session.room_id] = session
        return session

    @staticmethod
    def _now() -> datetime:
        """Return the current UTC timestamp for playback transitions."""

        return datetime.now(UTC)
