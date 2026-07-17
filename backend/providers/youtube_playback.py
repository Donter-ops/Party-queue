from __future__ import annotations

import re
from urllib.parse import parse_qs, urlparse


class YouTubePlaybackProvider:
    """Utility provider for YouTube web playback metadata.

    PartyQueue's playback engine already resolves a provider match but remains
    intentionally transport-agnostic. This helper translates the resolved
    YouTube-oriented identifiers into concrete video ids that the frontend can
    pass to the official YouTube IFrame Player API.
    """

    _VIDEO_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{11}$")

    def resolve_video_id(
        self,
        provider_track_id: str | None,
        external_url: str | None,
    ) -> str | None:
        """Return a playable YouTube video id when one can be determined.

        Resolution is intentionally conservative. If the existing playback
        pipeline produced a placeholder search token rather than a real YouTube
        id, this method returns ``None`` so the frontend can avoid attempting
        to load an invalid embedded player target.
        """

        if provider_track_id and self._is_video_id(provider_track_id):
            return provider_track_id

        if external_url:
            return self._extract_video_id_from_url(external_url)

        return None

    @classmethod
    def _extract_video_id_from_url(cls, url: str) -> str | None:
        """Extract a YouTube video id from supported web and music URLs."""

        parsed = urlparse(url)
        if parsed.netloc not in {"music.youtube.com", "www.youtube.com", "youtube.com", "youtu.be"}:
            return None

        if parsed.netloc == "youtu.be":
            video_id = parsed.path.lstrip("/").split("/", 1)[0]
            return video_id if cls._is_video_id(video_id) else None

        query_params = parse_qs(parsed.query)
        video_id = query_params.get("v", [None])[0]
        if cls._is_video_id(video_id):
            return video_id

        path_parts = [part for part in parsed.path.split("/") if part]
        if len(path_parts) >= 2 and path_parts[0] in {"embed", "shorts"}:
            candidate = path_parts[1]
            return candidate if cls._is_video_id(candidate) else None

        return None

    @classmethod
    def _is_video_id(cls, value: str | None) -> bool:
        """Return whether the value looks like a concrete YouTube video id."""

        return bool(value and cls._VIDEO_ID_PATTERN.fullmatch(value))
