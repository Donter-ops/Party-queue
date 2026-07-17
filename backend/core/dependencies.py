from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from agents.orchestrator_agent import OrchestratorAgent
from auth.spotify_auth import SpotifyAuthService
from auth.spotify_playback_client import SpotifyPlaybackClient
from auth.spotify_session import SpotifySessionStore
from auth.spotify_tokens import SpotifyOAuthConfig, SpotifyTokenService
from core.database import get_db
from decision.confidence import ConfidenceHelper
from providers.local import LocalSearchProvider
from providers.base import MusicProvider
from providers.musicbrainz import MusicBrainzProvider
from providers.spotify import SpotifyProvider
from providers.youtube import YouTubeProvider
from playback.host_provider import HostCapabilities, HostProvider
from playback.playback_engine import PlaybackEngine
from playback.playback_resolver import PlaybackResolver
from playback.playback_strategy import PlaybackStrategy
from playback.provider_resolver import ProviderResolver
from providers.youtube_playback import YouTubePlaybackProvider
from services.input_resolver import InputResolverService
from services.playback_service import PlaybackService
from services.queue_service import QueueService
from services.resolver_service import SongResolverService
from services.search_service import SearchService
from services.song_service import SongService
from tools.metadata_tool import MetadataTool
from tools.queue_tool import QueueTool
from tools.search_tool import SearchTool

DbSession = Annotated[Session, Depends(get_db)]
_spotify_session_store = SpotifySessionStore()


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


def get_queue_service(db: DbSession) -> QueueService:
    return QueueService(db)


def get_spotify_session_store() -> SpotifySessionStore:
    """Return the singleton in-memory Spotify host session store."""

    return _spotify_session_store


def get_spotify_oauth_config() -> SpotifyOAuthConfig:
    """Return Spotify OAuth configuration from environment variables."""

    import os

    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    if not client_id:
        raise RuntimeError("SPOTIFY_CLIENT_ID is missing.")

    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    if not client_secret:
        raise RuntimeError("SPOTIFY_CLIENT_SECRET is missing.")

    return SpotifyOAuthConfig(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=os.getenv("SPOTIFY_REDIRECT_URI", "http://127.0.0.1:8000/auth/spotify/callback"),
        frontend_redirect_uri=os.getenv("FRONTEND_SPOTIFY_REDIRECT_URI", "http://127.0.0.1:5173/connect-spotify"),
        scope=os.getenv(
            "SPOTIFY_SCOPE",
            "user-read-private user-read-email user-modify-playback-state user-read-playback-state user-read-currently-playing",
        ),
    )


def validate_spotify_oauth_config() -> None:
    """Fail fast during startup when required Spotify credentials are missing."""

    get_spotify_oauth_config()


def get_spotify_token_service(
    config: Annotated[SpotifyOAuthConfig, Depends(get_spotify_oauth_config)],
) -> SpotifyTokenService:
    """Create the Spotify token service."""

    return SpotifyTokenService(config)


def get_spotify_auth_service(
    config: Annotated[SpotifyOAuthConfig, Depends(get_spotify_oauth_config)],
    token_service: Annotated[SpotifyTokenService, Depends(get_spotify_token_service)],
) -> SpotifyAuthService:
    """Create the Spotify OAuth coordinator service."""

    return SpotifyAuthService(
        config=config,
        token_service=token_service,
        session_store=get_spotify_session_store(),
    )


def get_host_capabilities() -> HostCapabilities:
    """Return the future host playback capabilities for the local environment."""

    spotify_enabled = get_spotify_session_store().spotify_enabled
    supported_providers = (
        (
            HostProvider.SPOTIFY,
            HostProvider.YOUTUBE_MUSIC,
            HostProvider.APPLE_MUSIC,
        )
        if spotify_enabled
        else (
            HostProvider.YOUTUBE_MUSIC,
            HostProvider.APPLE_MUSIC,
        )
    )

    return HostCapabilities(
        supported_providers=supported_providers,
        preferred_provider=HostProvider.SPOTIFY if spotify_enabled else HostProvider.YOUTUBE_MUSIC,
        spotify_enabled=spotify_enabled,
    )


def get_playback_strategy() -> PlaybackStrategy:
    """Create the provider-independent playback planning strategy."""

    return PlaybackStrategy()


def get_provider_resolver() -> ProviderResolver:
    """Create the provider-specific playback resolver layer."""

    return ProviderResolver(
        spotify_provider=SpotifyProvider(),
        youtube_provider=YouTubeProvider(),
    )


def get_playback_resolver(
    playback_strategy: Annotated[PlaybackStrategy, Depends(get_playback_strategy)],
    provider_resolver: Annotated[ProviderResolver, Depends(get_provider_resolver)],
) -> PlaybackResolver:
    """Create the top-level playback resolver used by the engine."""

    return PlaybackResolver(
        playback_strategy=playback_strategy,
        provider_resolver=provider_resolver,
    )


def get_spotify_playback_client(
    token_service: Annotated[SpotifyTokenService, Depends(get_spotify_token_service)],
) -> SpotifyPlaybackClient:
    """Create the concrete Spotify playback client for host device control."""

    return SpotifyPlaybackClient(
        token_service=token_service,
        session_store=get_spotify_session_store(),
    )


def get_playback_engine(
    queue_service: Annotated[QueueService, Depends(get_queue_service)],
    playback_resolver: Annotated[PlaybackResolver, Depends(get_playback_resolver)],
    host_capabilities: Annotated[HostCapabilities, Depends(get_host_capabilities)],
    spotify_playback_client: Annotated[SpotifyPlaybackClient, Depends(get_spotify_playback_client)],
) -> PlaybackEngine:
    """Create the provider-agnostic playback engine for room sessions."""

    return PlaybackEngine(
        queue_service=queue_service,
        playback_resolver=playback_resolver,
        host_capabilities=host_capabilities,
        spotify_playback_client=spotify_playback_client,
    )


def get_youtube_playback_provider() -> YouTubePlaybackProvider:
    """Create the YouTube playback metadata helper for the web player."""

    return YouTubePlaybackProvider()


def get_playback_service(
    playback_engine: Annotated[PlaybackEngine, Depends(get_playback_engine)],
    queue_service: Annotated[QueueService, Depends(get_queue_service)],
    youtube_playback_provider: Annotated[YouTubePlaybackProvider, Depends(get_youtube_playback_provider)],
) -> PlaybackService:
    """Create the playback application service used by API routes."""

    return PlaybackService(
        playback_engine=playback_engine,
        queue_service=queue_service,
        youtube_playback_provider=youtube_playback_provider,
    )


def get_song_resolver_service(
    orchestrator_agent: Annotated[OrchestratorAgent, Depends(get_orchestrator_agent)],
    host_capabilities: Annotated[HostCapabilities, Depends(get_host_capabilities)],
) -> SongResolverService:
    """Create the song resolver service backed by the orchestration agent."""

    return SongResolverService(
        orchestrator_agent=orchestrator_agent,
        host_capabilities=host_capabilities,
        spotify_provider=SpotifyProvider(),
        youtube_provider=YouTubeProvider(),
    )


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


def get_input_resolver_service(
    orchestrator_agent: Annotated[OrchestratorAgent, Depends(get_orchestrator_agent)],
) -> InputResolverService:
    """Create the universal song input resolver service."""

    return InputResolverService(
        orchestrator_agent=orchestrator_agent,
        spotify_provider=SpotifyProvider(),
        youtube_provider=YouTubeProvider(),
    )
