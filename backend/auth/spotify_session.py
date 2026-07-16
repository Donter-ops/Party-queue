from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta


@dataclass(slots=True)
class SpotifySession:
    """Authenticated Spotify host session.

    The session stores the OAuth credentials needed for future Spotify-backed
    host playback actions. It intentionally contains no playback logic; it is
    purely an authentication boundary that later playback integrations can
    consume.
    """

    access_token: str
    refresh_token: str
    expires_at: datetime
    scope: str = ""
    token_type: str = "Bearer"


class SpotifySessionStore:
    """In-memory store for Spotify OAuth state and host session data.

    The current PartyQueue architecture is single-host and does not yet require
    persistent user accounts. This store therefore keeps one host session and a
    short-lived set of pending OAuth states in memory.
    """

    _current_session: SpotifySession | None = None
    _pending_states: dict[str, datetime] = {}
    _state_ttl = timedelta(minutes=10)

    def create_state(self) -> str:
        """Create and register a CSRF-protection state token."""

        state = secrets.token_urlsafe(24)
        self._pending_states[state] = datetime.now(UTC) + self._state_ttl
        self._prune_expired_states()
        return state

    def consume_state(self, state: str) -> bool:
        """Validate and consume a previously issued OAuth state token."""

        self._prune_expired_states()
        expires_at = self._pending_states.pop(state, None)
        return expires_at is not None and expires_at >= datetime.now(UTC)

    def set_session(self, session: SpotifySession) -> SpotifySession:
        """Persist the authenticated Spotify host session."""

        self._current_session = session
        return session

    def get_session(self) -> SpotifySession | None:
        """Return the active Spotify session when available."""

        return self._current_session

    @property
    def spotify_enabled(self) -> bool:
        """Whether the host currently has a connected Spotify session."""

        return self._current_session is not None and self._current_session.expires_at > datetime.now(UTC)

    def _prune_expired_states(self) -> None:
        """Discard expired OAuth state tokens."""

        now = datetime.now(UTC)
        self._pending_states = {
            state: expires_at
            for state, expires_at in self._pending_states.items()
            if expires_at >= now
        }
