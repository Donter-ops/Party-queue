from __future__ import annotations

import html
import json
import os
import re
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote_plus, urlencode, urlparse
from urllib.request import Request, urlopen

from providers.base import MusicProvider, ProviderSong


class YouTubeProvider(MusicProvider):
    """YouTube catalog provider for resolution and cross-provider matching.

    The provider prefers the official YouTube Data API when a
    ``YOUTUBE_API_KEY`` is configured. For local development without a key it
    falls back to parsing public YouTube search results, which keeps the MVP
    usable while preserving the same provider interface.
    """

    SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
    OEMBED_URL = "https://www.youtube.com/oembed"
    PUBLIC_SEARCH_URL = "https://www.youtube.com/results"
    VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"
    REQUEST_TIMEOUT_SECONDS = 10
    USER_AGENT = "PartyQueue/1.0"
    _VIDEO_ID_PATTERN = re.compile(r'"videoId":"([A-Za-z0-9_-]{11})"')

    def search(self, query: str) -> list[ProviderSong]:
        """Search YouTube videos for a song-oriented query."""

        normalized_query = query.strip()
        if not normalized_query:
            return []

        api_key = os.getenv("YOUTUBE_API_KEY", "").strip()
        if api_key:
            return self._search_with_data_api(normalized_query, api_key)
        return self._search_public_results(normalized_query)

    def resolve(self, url: str) -> ProviderSong:
        """Resolve a YouTube or YouTube Music URL into a provider song."""

        video_id = self._extract_video_id(url)
        if not video_id:
            raise ValueError("Unsupported YouTube URL.")
        song = self.get_song(video_id)
        if song.external_url is None:
            song.external_url = self._build_watch_url(video_id)
        return song

    def get_song(self, provider_id: str) -> ProviderSong:
        """Fetch lightweight public metadata for a YouTube video."""

        watch_url = self._build_watch_url(provider_id)
        oembed_url = f"{self.OEMBED_URL}?{urlencode({'url': watch_url, 'format': 'json'})}"
        request = Request(
            oembed_url,
            headers={"User-Agent": self.USER_AGENT},
            method="GET",
        )

        try:
            with urlopen(request, timeout=self.REQUEST_TIMEOUT_SECONDS) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, json.JSONDecodeError) as error:
            raise RuntimeError("YouTube metadata request failed.") from error

        return ProviderSong(
            provider="youtube",
            provider_id=provider_id,
            title=str(payload.get("title", "")).strip() or f"YouTube Video {provider_id}",
            artist=str(payload.get("author_name", "")).strip() or "Unknown Artist",
            external_url=watch_url,
            confidence=1.0,
        )

    def _search_with_data_api(self, query: str, api_key: str) -> list[ProviderSong]:
        """Search YouTube using the official Data API."""

        request_url = (
            f"{self.SEARCH_URL}?{urlencode({'part': 'snippet', 'q': query, 'type': 'video', 'maxResults': 10, 'key': api_key})}"
        )
        request = Request(
            request_url,
            headers={"User-Agent": self.USER_AGENT},
            method="GET",
        )

        try:
            with urlopen(request, timeout=self.REQUEST_TIMEOUT_SECONDS) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, json.JSONDecodeError):
            return []

        items = payload.get("items", [])
        video_ids = [
            str(item.get("id", {}).get("videoId", "")).strip()
            for item in items
            if str(item.get("id", {}).get("videoId", "")).strip()
        ]
        video_details = self._fetch_video_details(video_ids=video_ids, api_key=api_key)
        songs: list[ProviderSong] = []
        for index, item in enumerate(items):
            video_id = str(item.get("id", {}).get("videoId", "")).strip()
            if not video_id:
                continue
            snippet = item.get("snippet", {})
            detail = video_details.get(video_id, {})
            channel_title = str(snippet.get("channelTitle", "")).strip()
            songs.append(
                ProviderSong(
                    provider="youtube",
                    provider_id=video_id,
                    title=html.unescape(str(snippet.get("title", "")).strip()),
                    artist=channel_title or "Unknown Artist",
                    external_url=self._build_watch_url(video_id),
                    confidence=max(0.45, 1.0 - (index * 0.06)),
                    duration_seconds=self._parse_duration_seconds(
                        detail.get("contentDetails", {}).get("duration")
                    ),
                    channel_title=channel_title or None,
                    is_official_artist=self._looks_official_artist_channel(channel_title),
                    is_official_music_channel=self._looks_music_channel(channel_title),
                )
            )
        return songs

    def _search_public_results(self, query: str) -> list[ProviderSong]:
        """Search public YouTube results pages when no API key is configured."""

        request_url = f"{self.PUBLIC_SEARCH_URL}?search_query={quote_plus(query)}"
        request = Request(
            request_url,
            headers={"User-Agent": self.USER_AGENT},
            method="GET",
        )

        try:
            with urlopen(request, timeout=self.REQUEST_TIMEOUT_SECONDS) as response:
                payload = response.read().decode("utf-8", errors="replace")
        except (HTTPError, URLError):
            return []

        video_ids: list[str] = []
        for match in self._VIDEO_ID_PATTERN.finditer(payload):
            video_id = match.group(1)
            if video_id not in video_ids:
                video_ids.append(video_id)
            if len(video_ids) >= 10:
                break

        results: list[ProviderSong] = []
        for index, video_id in enumerate(video_ids):
            try:
                song = self.get_song(video_id)
            except RuntimeError:
                continue
            song.confidence = max(0.45, 0.9 - (index * 0.08))
            song.title = html.unescape(song.title)
            song.artist = html.unescape(song.artist)
            song.channel_title = song.artist
            song.is_official_artist = self._looks_official_artist_channel(song.artist)
            song.is_official_music_channel = self._looks_music_channel(song.artist)
            results.append(song)
        return results

    def _fetch_video_details(self, video_ids: list[str], api_key: str) -> dict[str, dict]:
        """Fetch detailed metadata for candidate videos via the Data API."""

        if not video_ids:
            return {}

        request_url = (
            f"{self.VIDEOS_URL}?{urlencode({'part': 'snippet,contentDetails', 'id': ','.join(video_ids), 'key': api_key})}"
        )
        request = Request(
            request_url,
            headers={"User-Agent": self.USER_AGENT},
            method="GET",
        )

        try:
            with urlopen(request, timeout=self.REQUEST_TIMEOUT_SECONDS) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except (HTTPError, URLError, json.JSONDecodeError):
            return {}

        return {
            str(item.get("id", "")).strip(): item
            for item in payload.get("items", [])
            if str(item.get("id", "")).strip()
        }

    @staticmethod
    def _build_watch_url(video_id: str) -> str:
        """Return a canonical watch URL for a YouTube video id."""

        return f"https://www.youtube.com/watch?v={video_id}"

    @staticmethod
    def _parse_duration_seconds(raw_duration: object) -> int | None:
        """Parse an ISO 8601 YouTube duration into seconds."""

        if not isinstance(raw_duration, str) or not raw_duration:
            return None
        pattern = re.compile(
            r"^P(?:(?P<days>\d+)D)?(?:T(?:(?P<hours>\d+)H)?(?:(?P<minutes>\d+)M)?(?:(?P<seconds>\d+)S)?)?$"
        )
        match = pattern.fullmatch(raw_duration)
        if match is None:
            return None
        days = int(match.group("days") or 0)
        hours = int(match.group("hours") or 0)
        minutes = int(match.group("minutes") or 0)
        seconds = int(match.group("seconds") or 0)
        return (days * 86400) + (hours * 3600) + (minutes * 60) + seconds

    @staticmethod
    def _looks_official_artist_channel(channel_title: str) -> bool:
        """Heuristic for official artist-owned channels."""

        lowered = channel_title.strip().lower()
        return any(marker in lowered for marker in ("official", "vevo"))

    @staticmethod
    def _looks_music_channel(channel_title: str) -> bool:
        """Heuristic for auto-generated and music-topic channels."""

        lowered = channel_title.strip().lower()
        return "topic" in lowered or "music" in lowered

    @staticmethod
    def _extract_video_id(value: str) -> str | None:
        """Extract a YouTube video id from common URL forms."""

        parsed = urlparse(value)
        if parsed.netloc == "youtu.be":
            candidate = parsed.path.lstrip("/").split("/", 1)[0]
            return candidate or None

        if parsed.netloc not in {"music.youtube.com", "www.youtube.com", "youtube.com"}:
            return None

        query_params = parse_qs(parsed.query)
        video_id = query_params.get("v", [None])[0]
        if video_id:
            return video_id

        path_parts = [part for part in parsed.path.split("/") if part]
        if len(path_parts) >= 2 and path_parts[0] in {"embed", "shorts"}:
            return path_parts[1]
        return None
