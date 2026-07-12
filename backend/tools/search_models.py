from __future__ import annotations

from dataclasses import dataclass, field

from providers.base import ProviderSong


@dataclass(slots=True)
class SearchRequest:
    """Typed request passed from agents into the search tool.

    The request object isolates search intent from concrete provider APIs. This
    allows future AI agents to refine or expand search parameters without
    changing the tool contract or orchestration pipeline.
    """

    query: str
    provider: str = "local"
    limit: int = 5
    source_hint: str | None = None


@dataclass(slots=True)
class SearchResult:
    """Typed result returned by the search tool.

    The result keeps the search output structured and provider-neutral so later
    decision stages can reason over candidate matches without depending on a
    specific provider implementation.
    """

    query: str
    provider: str
    matches: list[ProviderSong] = field(default_factory=list)
    total_matches: int = 0
