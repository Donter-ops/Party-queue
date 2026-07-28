from __future__ import annotations

import base64
import json
import os
import time
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from providers.base import MusicProvider, ProviderSong


@dataclass(slots=True)
class SpotifyCatalogToken:
    """Short-lived app token for Spotify catalog access."""

    access_token: str
    expires_at: float


class SpotifyProvider(MusicProvider):
    """Spotify catalog provider backed by the official Web API.

    The provider uses the client credentials flow for catalog metadata and
    search. This avoids any dependency on host playback OAuth while still
    allowing PartyQueue to turn Spotify links or general song metadata into a
    provider-normalized track candidate.
    """

    TOKEN_URL = "https://accounts.spotify.com/api/token"
    TRACK_URL_TEMPLATE = "https://api.spotify.com/v1/tracks/{track_id}"
    SEARCH_URL = "https://api.spotify.com/v1/search"
    REQUEST_TIMEOUT_SECONDS = 10

    _catalog_token: SpotifyCatalogToken | None = None

    def search(self, query: str) -> list[ProviderSong]:
        """Search Spotify tracks using the official catalog search endpoint."""

        normalized_query = query.strip()
        if not normalized_query:
            return []

        payload = self._request_json(
            "GET",
            f"{self.SEARCH_URL}?{urlencode({'q': normalized_query, 'type': 'track', 'limit': 5, 'market': 'DE'})}",
        )
        items = payload.get("tracks", {}).get("items", [])
        return [self._map_track(track, default_confidence=max(0.45, 1.0 - (index * 0.08))) for index, track in enumerate(items)]

    def resolve(self, url: str) -> ProviderSong:
        """Resolve a Spotify track URL or URI into normalized metadata."""

        track_id = self._extract_track_id(url)
        if not track_id:
            raise ValueError("Unsupported Spotify track URL.")
        return self.get_song(track_id)

    def get_song(self, provider_id: str) -> ProviderSong:
        """Fetch one Spotify track by its provider identifier."""

        payload = self._request_json("GET", self.TRACK_URL_TEMPLATE.format(track_id=provider_id))
        return self._map_track(payload, default_confidence=1.0)

    def _request_json(self, method: str, url: str) -> dict:
        """Execute a Spotify catalog request using a cached app token."""

        token = self._get_catalog_token()
        request = Request(
            url,
            headers={"Authorization": f"Bearer {token}"},
            method=method,
        )

        try:
            with urlopen(request, timeout=self.REQUEST_TIMEOUT_SECONDS) as response:
                return json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, json.JSONDecodeError) as error:
            raise RuntimeError("Spotify catalog request failed.") from error

    def _get_catalog_token(self) -> str:
        """Return a cached Spotify client-credentials token."""

        token = self._catalog_token
        if token and token.expires_at > time.time() + 30:
            return token.access_token

        client_id = os.getenv("SPOTIFY_CLIENT_ID")
        client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
        if not client_id:
            raise RuntimeError("SPOTIFY_CLIENT_ID is missing.")
        if not client_secret:
            raise RuntimeError("SPOTIFY_CLIENT_SECRET is missing.")

        basic_token = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("utf-8")
        body = urlencode({"grant_type": "client_credentials"}).encode("utf-8")
        request = Request(
            self.TOKEN_URL,
            data=body,
            headers={
                "Authorization": f"Basic {basic_token}",
                "Content-Type": "application/x-www-form-urlencoded",
            },
            method="POST",
        )

        try:
            with urlopen(request, timeout=self.REQUEST_TIMEOUT_SECONDS) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, json.JSONDecodeError) as error:
            raise RuntimeError("Spotify client credentials request failed.") from error

        self._catalog_token = SpotifyCatalogToken(
            access_token=str(payload["access_token"]),
            expires_at=time.time() + int(payload.get("expires_in", 3600)),
        )
        return self._catalog_token.access_token

    @staticmethod
    def _map_track(track: dict, *, default_confidence: float) -> ProviderSong:
        """Normalize one Spotify track payload into a provider song."""

        artists = track.get("artists", [])
        artist_list = [
            str(artist.get("name", "")).strip()
            for artist in artists
            if str(artist.get("name", "")).strip()
        ]
        artist_names = ", ".join(artist_list)
        external_url = str(track.get("external_urls", {}).get("spotify", "")).strip() or None
        popularity = track.get("popularity")
        confidence = default_confidence
        duration_ms = SpotifyProvider._extract_duration_ms(track.get("duration_ms"))
        if isinstance(popularity, int):
            confidence = max(default_confidence, min(1.0, popularity / 100.0))

        return ProviderSong(
            provider="spotify",
            provider_id=str(track.get("id", "")).strip(),
            title=str(track.get("name", "")).strip(),
            artist=artist_names or "Unknown Artist",
            external_url=external_url,
            confidence=confidence,
            artists=artist_list or None,
            album=str(track.get("album", {}).get("name", "")).strip() or None,
            duration_ms=duration_ms,
            duration_seconds=self._extract_duration_seconds(duration_ms),
            isrc=str(track.get("external_ids", {}).get("isrc", "")).strip() or None,
        )

    @staticmethod
    def _extract_duration_ms(raw_duration_ms: object) -> int | None:
        """Normalize Spotify duration milliseconds."""

        try:
            duration_ms = int(raw_duration_ms)
        except (TypeError, ValueError):
            return None
        return max(0, duration_ms)

    @staticmethod
    def _extract_duration_seconds(raw_duration_ms: object) -> int | None:
        """Convert Spotify duration milliseconds into rounded seconds."""

        duration_ms = SpotifyProvider._extract_duration_ms(raw_duration_ms)
        if duration_ms is None:
            return None
        return max(0, round(duration_ms / 1000))

    @staticmethod
    def _extract_track_id(value: str) -> str | None:
        """Extract a Spotify track id from URL or URI input."""

        if value.startswith("spotify:track:"):
            track_id = value.removeprefix("spotify:track:").strip()
            return track_id or None

        parsed = urlparse(value)
        if "open.spotify.com" not in parsed.netloc:
            return None

        path_parts = [part for part in parsed.path.split("/") if part]
        if len(path_parts) >= 2 and path_parts[0] == "track":
            return path_parts[1]
        return None
