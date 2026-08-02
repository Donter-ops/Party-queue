from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from auth.spotify_session import SpotifySession, SpotifySessionStore
from auth.spotify_tokens import SpotifyTokenService


class SpotifyPlaybackError(RuntimeError):
    """Structured Spotify playback failure used by the playback engine.

    The playback layer needs user-facing failure reasons without leaking raw
    HTTP details into services or routes. This exception standardizes those
    messages so callers can surface actionable playback errors while the
    implementation still talks directly to the Spotify Web API.
    """


@dataclass(frozen=True, slots=True)
class SpotifyDevice:
    """Normalized Spotify Connect device information.

    Only the fields currently required by PartyQueue playback are exposed.
    Additional device metadata can be added later without changing the engine
    contract that selects a target playback device.
    """

    device_id: str
    device_name: str
    is_active: bool


class SpotifyPlaybackClient:
    """Concrete Spotify Web API client for host playback actions.

    This client encapsulates Spotify device discovery and track playback while
    reusing the existing OAuth session store and token refresh service. The
    rest of the playback architecture remains provider-agnostic and consumes
    only normalized results or explicit playback failures.
    """

    DEVICES_URL = "https://api.spotify.com/v1/me/player/devices"
    PLAY_URL = "https://api.spotify.com/v1/me/player/play"
    REQUEST_TIMEOUT_SECONDS = 10

    def __init__(
        self,
        token_service: SpotifyTokenService,
        session_store: SpotifySessionStore,
    ) -> None:
        self.token_service = token_service
        self.session_store = session_store

    def get_available_devices(self) -> list[SpotifyDevice]:
        """Fetch the host's available Spotify Connect devices.

        Raises:
            SpotifyPlaybackError: When the host is not authenticated, the token
                cannot be refreshed, Spotify access is unavailable, or no
                playable devices are exposed by Spotify.
        """

        payload = self._request_json("GET", self.DEVICES_URL)
        devices_payload = payload.get("devices", [])
        devices = [
            SpotifyDevice(
                device_id=str(device["id"]),
                device_name=str(device["name"]),
                is_active=bool(device.get("is_active", False)),
            )
            for device in devices_payload
            if device.get("id")
        ]
        if not devices:
            raise SpotifyPlaybackError("No available Spotify device found.")
        return devices

    def play_track(self, device_id: str, spotify_track_id: str) -> None:
        """Start Spotify playback for a specific track on a selected device.

        Args:
            device_id: Spotify Connect target device identifier.
            spotify_track_id: Track identifier or URI resolved by playback.

        Raises:
            SpotifyPlaybackError: When playback cannot be started because the
                host lacks Premium, no active device is usable, the token is
                invalid, or Spotify rejects the command.
        """

        track_uri = self._normalize_track_uri(spotify_track_id)
        play_url = f"{self.PLAY_URL}?{urlencode({'device_id': device_id})}"
        self._request_json(
            "PUT",
            play_url,
            body={"uris": [track_uri]},
            expect_json=False,
        )

    def _request_json(
        self,
        method: str,
        url: str,
        body: dict[str, object] | None = None,
        expect_json: bool = True,
        retry_on_unauthorized: bool = True,
    ) -> dict:
        """Execute a Spotify Web API request with token refresh support."""

        session = self._get_valid_session()
        headers = {
            "Authorization": f"Bearer {session.access_token}",
        }
        request_body = None
        if body is not None:
            headers["Content-Type"] = "application/json"
            request_body = json.dumps(body).encode("utf-8")

        request = Request(url, data=request_body, headers=headers, method=method)

        try:
            with urlopen(request, timeout=self.REQUEST_TIMEOUT_SECONDS) as response:
                if not expect_json:
                    return {}
                raw_payload = response.read()
                if not raw_payload:
                    return {}
                return json.loads(raw_payload.decode("utf-8"))
        except HTTPError as error:
            if error.code == 401 and retry_on_unauthorized:
                self._refresh_session_or_raise(session)
                return self._request_json(
                    method=method,
                    url=url,
                    body=body,
                    expect_json=expect_json,
                    retry_on_unauthorized=False,
                )
            raise self._map_http_error(error) from error
        except URLError as error:
            raise SpotifyPlaybackError("Spotify playback request failed.") from error
        except json.JSONDecodeError as error:
            raise SpotifyPlaybackError("Spotify returned an invalid response.") from error

    def _get_valid_session(self) -> SpotifySession:
        """Return a valid Spotify session or refresh it when expired."""

        session = self.session_store.get_session()
        if session is None:
            raise SpotifyPlaybackError("Spotify host is not connected.")
        if session.expires_at <= datetime.now(UTC):
            return self._refresh_session_or_raise(session)
        return session

    def _refresh_session_or_raise(self, session: SpotifySession) -> SpotifySession:
        """Refresh the current Spotify session and persist the new tokens."""

        try:
            refreshed_session = self.token_service.refresh_session(session.refresh_token)
        except RuntimeError as error:
            raise SpotifyPlaybackError("Spotify token expired. Please reconnect Spotify.") from error
        self.session_store.set_session(refreshed_session)
        return refreshed_session

    @staticmethod
    def _normalize_track_uri(spotify_track_id: str) -> str:
        """Convert a track identifier into the Spotify URI expected by playback."""

        if spotify_track_id.startswith("spotify:track:"):
            return spotify_track_id
        if spotify_track_id.startswith("http://") or spotify_track_id.startswith("https://"):
            parsed = urlparse(spotify_track_id)
            hostname = parsed.hostname or ""
            if hostname.lower() == "open.spotify.com":
                path_parts = [part for part in parsed.path.split("/") if part]
                if len(path_parts) >= 2 and path_parts[0] == "track":
                    return f"spotify:track:{path_parts[1]}"
        return f"spotify:track:{spotify_track_id}"

    @staticmethod
    def _map_http_error(error: HTTPError) -> SpotifyPlaybackError:
        """Translate Spotify HTTP failures into stable playback messages."""

        if error.code == 401:
            return SpotifyPlaybackError("Spotify token expired. Please reconnect Spotify.")
        if error.code == 403:
            return SpotifyPlaybackError("Spotify Premium is required for host playback.")
        if error.code == 404:
            return SpotifyPlaybackError("No active Spotify device found.")
        if error.code == 429:
            return SpotifyPlaybackError("Spotify rate limit reached. Please try again.")
        return SpotifyPlaybackError("Spotify playback request failed.")
