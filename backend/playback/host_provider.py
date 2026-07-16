from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class HostProvider(StrEnum):
    """Known host playback targets supported by the abstraction layer.

    The enum captures future playback surfaces without binding the system to any
    one provider implementation today. It allows strategy code to talk about
    playback destinations in a stable, provider-independent way.
    """

    SPOTIFY = "spotify"
    YOUTUBE_MUSIC = "youtube_music"
    APPLE_MUSIC = "apple_music"


@dataclass(frozen=True, slots=True)
class HostCapabilities:
    """Static description of which playback hosts are available on a device.

    PlaybackStrategy consumes this model to decide how a canonical song should
    be matched to a future host provider. The model contains no transport logic
    and makes no network calls, keeping playback planning deterministic.
    """

    supported_providers: tuple[HostProvider, ...]
    preferred_provider: HostProvider | None = None
    spotify_enabled: bool = False
