from __future__ import annotations

from enum import StrEnum


class DecisionStrategy(StrEnum):
    """Enumeration of orchestration strategies for playable-source decisions.

    The enum is intentionally narrow and explicit so future agents can reason
    about strategy selection without depending on provider-specific branches
    scattered throughout the codebase.
    """

    DIRECT_PLAYBACK = "DIRECT_PLAYBACK"
    SEARCH_EQUIVALENT = "SEARCH_EQUIVALENT"
    REQUEST_USER_INPUT = "REQUEST_USER_INPUT"
    NO_PLAYABLE_SOURCE = "NO_PLAYABLE_SOURCE"
