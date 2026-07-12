from __future__ import annotations

from tools.search_models import SearchRequest, SearchResult
from agents.orchestrator_agent import OrchestratorAgent


class SearchService:
    """Service boundary for catalog search workflows.

    The service keeps HTTP routers decoupled from the orchestration and tool
    layers. Routers pass only the user query, while the service is responsible
    for constructing the typed search request that flows through the backend
    agent architecture.
    """

    def __init__(self, orchestrator_agent: OrchestratorAgent) -> None:
        self.orchestrator_agent = orchestrator_agent

    def search(self, query: str, limit: int = 5) -> SearchResult:
        """Search the local provider catalog through the orchestration layer."""

        request = SearchRequest(
            query=query.strip(),
            provider="musicbrainz",
            limit=limit,
            source_hint="search_api",
        )
        return self.orchestrator_agent.search(request)
