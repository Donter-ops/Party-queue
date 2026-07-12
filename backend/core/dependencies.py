from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from agents.orchestrator_agent import OrchestratorAgent
from core.database import get_db
from decision.confidence import ConfidenceHelper
from providers.local import LocalSearchProvider
from providers.base import MusicProvider
from providers.musicbrainz import MusicBrainzProvider
from providers.spotify import SpotifyProvider
from providers.youtube import YouTubeProvider
from playback.playback_engine import PlaybackEngine
from services.queue_service import QueueService
from services.resolver_service import SongResolverService
from services.search_service import SearchService
from services.song_service import SongService
from tools.metadata_tool import MetadataTool
from tools.queue_tool import QueueTool
from tools.search_tool import SearchTool

DbSession = Annotated[Session, Depends(get_db)]


def get_confidence_helper() -> ConfidenceHelper:
    """Create the confidence helper used by decision-aware agents."""
    return ConfidenceHelper()


def get_music_providers() -> dict[str, MusicProvider]:
    """Return the provider registry used by backend tools."""
    return {
        "spotify": SpotifyProvider(),
        "youtube": YouTubeProvider(),
    }


def get_search_providers() -> dict[str, MusicProvider]:
    """Return the provider registry used by the search tool."""
    musicbrainz_provider = MusicBrainzProvider()
    return {
        "local": musicbrainz_provider,
        "musicbrainz": musicbrainz_provider,
    }


def get_search_tool(
    providers: Annotated[dict[str, MusicProvider], Depends(get_search_providers)],
) -> SearchTool:
    """Create the search tool with provider dependencies."""
    return SearchTool(providers)


def get_metadata_tool(
    providers: Annotated[dict[str, MusicProvider], Depends(get_music_providers)],
) -> MetadataTool:
    """Create the metadata tool with provider dependencies."""
    return MetadataTool(providers)


def get_queue_tool() -> QueueTool:
    """Create the queue tool used for queue-safe song preparation."""
    return QueueTool()


def get_orchestrator_agent(
    queue_tool: Annotated[QueueTool, Depends(get_queue_tool)],
    metadata_tool: Annotated[MetadataTool, Depends(get_metadata_tool)],
    search_tool: Annotated[SearchTool, Depends(get_search_tool)],
    confidence_helper: Annotated[ConfidenceHelper, Depends(get_confidence_helper)],
) -> OrchestratorAgent:
    """Create the orchestration agent used by backend services."""
    return OrchestratorAgent(
        queue_tool=queue_tool,
        metadata_tool=metadata_tool,
        search_tool=search_tool,
        confidence_helper=confidence_helper,
    )


def get_song_resolver_service(
    orchestrator_agent: Annotated[OrchestratorAgent, Depends(get_orchestrator_agent)],
) -> SongResolverService:
    """Create the song resolver service backed by the orchestration agent."""
    return SongResolverService(orchestrator_agent)


def get_queue_service(db: DbSession) -> QueueService:
    return QueueService(db)


def get_playback_engine(
    queue_service: Annotated[QueueService, Depends(get_queue_service)],
) -> PlaybackEngine:
    """Create the provider-agnostic playback engine for room sessions."""

    return PlaybackEngine(queue_service=queue_service)


def get_song_service(
    db: DbSession,
    resolver_service: Annotated[SongResolverService, Depends(get_song_resolver_service)],
) -> SongService:
    return SongService(db=db, resolver_service=resolver_service)


def get_search_service(
    orchestrator_agent: Annotated[OrchestratorAgent, Depends(get_orchestrator_agent)],
) -> SearchService:
    """Create the search service used by the search router."""

    return SearchService(orchestrator_agent=orchestrator_agent)
