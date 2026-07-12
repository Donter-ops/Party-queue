from __future__ import annotations

from providers.base import MusicProvider
from tools.base_tool import BaseTool
from tools.search_models import SearchRequest, SearchResult


class SearchTool(BaseTool):
    """Tool responsible for provider-backed search operations.

    The tool receives a typed `SearchRequest` and returns a typed
    `SearchResult`, creating a stable boundary for future cognitive and
    multi-agent workflows.
    """

    def __init__(self, providers: dict[str, MusicProvider]) -> None:
        self.providers = providers

    def run(self, payload: SearchRequest) -> SearchResult:
        """Execute a provider search request and return normalized results."""
        provider = self.providers[payload.provider]
        matches = provider.search(payload.query)[: payload.limit]
        confidence = 0.98 if matches else 0.0
        return SearchResult(
            query=payload.query,
            provider=payload.provider,
            matches=matches,
            total_matches=len(matches),
            confidence=confidence,
        )
