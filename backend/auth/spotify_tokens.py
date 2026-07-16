from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from auth.spotify_session import SpotifySession


@dataclass(frozen=True, slots=True)
class SpotifyOAuthConfig:
    """Runtime configuration for Spotify OAuth requests."""

    client_id: str
    client_secret: str
    redirect_uri: str
    frontend_redirect_uri: str
    scope: str


class SpotifyTokenService:
    """Token exchange and refresh helper for Spotify Authorization Code flow.

    This service handles the Spotify token endpoint only. It is deliberately
    isolated from routing so future authentication flows, refresh automation,
    and persistence changes can reuse the same token exchange logic.
    """

    TOKEN_URL = "https://accounts.spotify.com/api/token"
    REQUEST_TIMEOUT_SECONDS = 10

    def __init__(self, config: SpotifyOAuthConfig) -> None:
        self.config = config

    def exchange_code(self, code: str) -> SpotifySession:
        """Exchange an authorization code for a Spotify host session."""

        payload = self._post_token_request(
            {
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": self.config.redirect_uri,
            }
        )
        return self._build_session(payload)

    def refresh_session(self, refresh_token: str) -> SpotifySession:
        """Refresh a Spotify session using its refresh token."""

        payload = self._post_token_request(
            {
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
            }
        )
        if "refresh_token" not in payload:
            payload["refresh_token"] = refresh_token
        return self._build_session(payload)

    def _post_token_request(self, form_data: dict[str, str]) -> dict:
        """Send a form-encoded token request to Spotify."""

        client_credentials = f"{self.config.client_id}:{self.config.client_secret}".encode("utf-8")
        authorization_header = base64.b64encode(client_credentials).decode("utf-8")
        body = urlencode(form_data).encode("utf-8")
        request = Request(
            self.TOKEN_URL,
            data=body,
            headers={
                "Authorization": f"Basic {authorization_header}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.REQUEST_TIMEOUT_SECONDS) as response:
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, json.JSONDecodeError) as error:
            raise RuntimeError("Spotify token request failed.") from error

    @staticmethod
    def _build_session(payload: dict) -> SpotifySession:
        """Convert Spotify token JSON into a typed session object."""

        expires_in = int(payload.get("expires_in", 0))
        return SpotifySession(
            access_token=str(payload["access_token"]),
            refresh_token=str(payload["refresh_token"]),
            expires_at=datetime.now(UTC) + timedelta(seconds=expires_in),
            scope=str(payload.get("scope", "")),
            token_type=str(payload.get("token_type", "Bearer")),
        )
