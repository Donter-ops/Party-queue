from __future__ import annotations

import json
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from providers.base import MusicProvider, ProviderSong


class MusicBrainzProvider(MusicProvider):
    """MusicBrainz-backed provider for recording search.

    This provider integrates PartyQueue with the official MusicBrainz recording
    search API while keeping the rest of the architecture provider-agnostic. It
    implements only search for now; direct resolution and song fetching remain
    intentionally unsupported until a broader provider playback model exists.

    MusicBrainz expects a meaningful ``User-Agent`` and asks clients to be good
    citizens about request rates. This provider therefore uses a descriptive
    application identifier and enforces a conservative in-process rate limit of
    one request per second.
    """

    BASE_URL = "https://musicbrainz.org/ws/2/recording/"
    USER_AGENT = "PartyQueue/1.0 ( https://github.com/Donter-ops/Party-queue )"
    REQUEST_TIMEOUT_SECONDS = 10
    MIN_REQUEST_INTERVAL_SECONDS = 1.0

    _rate_limit_lock = threading.Lock()
    _last_request_at = 0.0

    def search(self, query: str) -> list[ProviderSong]:
        """Search MusicBrainz recordings and normalize the response."""

        normalized_query = query.strip()
        if not normalized_query:
            return []

        payload = self._perform_search_request(normalized_query)
        recordings = payload.get("recordings", [])
        return [self._map_recording(recording) for recording in recordings]

    def resolve(self, url: str) -> ProviderSong:
        """Resolve is not implemented for MusicBrainz yet."""

        raise NotImplementedError("MusicBrainzProvider does not resolve URLs yet.")

    def get_song(self, provider_id: str) -> ProviderSong:
        """Direct lookup is not implemented for MusicBrainz yet."""

        raise NotImplementedError("MusicBrainzProvider does not fetch songs by ID yet.")

    def _perform_search_request(self, query: str) -> dict:
        """Perform a rate-limited request against the MusicBrainz search API."""

        self._wait_for_rate_limit_slot()
        request_url = f"{self.BASE_URL}?{urlencode({'query': query, 'fmt': 'json', 'limit': 5, 'dismax': 'true'})}"
        request = Request(
            request_url,
            headers={
                "Accept": "application/json",
                "User-Agent": self.USER_AGENT,
            },
            method="GET",
        )

        try:
            with urlopen(request, timeout=self.REQUEST_TIMEOUT_SECONDS) as response:
                return json.loads(response.read().decode("utf-8"))
        except HTTPError as error:
            if error.code == 503:
                time.sleep(self.MIN_REQUEST_INTERVAL_SECONDS)
                with urlopen(request, timeout=self.REQUEST_TIMEOUT_SECONDS) as response:
                    return json.loads(response.read().decode("utf-8"))
            return {}
        except (URLError, TimeoutError, json.JSONDecodeError):
            return {}

    @classmethod
    def _wait_for_rate_limit_slot(cls) -> None:
        """Ensure requests are spaced to respect MusicBrainz rate guidance."""

        with cls._rate_limit_lock:
            current_time = time.monotonic()
            elapsed = current_time - cls._last_request_at
            if elapsed < cls.MIN_REQUEST_INTERVAL_SECONDS:
                time.sleep(cls.MIN_REQUEST_INTERVAL_SECONDS - elapsed)
            cls._last_request_at = time.monotonic()

    def _map_recording(self, recording: dict) -> ProviderSong:
        """Convert one MusicBrainz recording document into a provider song."""

        recording_id = str(recording.get("id", "")).strip()
        title = str(recording.get("title", "")).strip()
        artist = self._extract_artist_name(recording.get("artist-credit", []))
        score = self._normalize_confidence(recording.get("score"))

        return ProviderSong(
            provider="musicbrainz",
            provider_id=recording_id,
            title=title,
            artist=artist,
            external_url=f"https://musicbrainz.org/recording/{recording_id}" if recording_id else None,
            confidence=score,
        )

    @staticmethod
    def _extract_artist_name(artist_credit: list[dict]) -> str:
        """Flatten MusicBrainz artist-credit structures into one display string."""

        parts: list[str] = []
        for credit in artist_credit:
            name = str(
                credit.get("name")
                or credit.get("artist", {}).get("name")
                or ""
            ).strip()
            join_phrase = str(credit.get("joinphrase", ""))
            if name:
                parts.append(f"{name}{join_phrase}")
        return "".join(parts).strip()

    @staticmethod
    def _normalize_confidence(raw_score: object) -> float:
        """Normalize MusicBrainz score strings into floats between 0 and 1."""

        try:
            numeric_score = float(raw_score)
        except (TypeError, ValueError):
            return 0.0
        return max(0.0, min(1.0, numeric_score / 100.0))
