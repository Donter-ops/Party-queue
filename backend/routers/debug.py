from __future__ import annotations

import base64
from dataclasses import asdict
import json
import os
import traceback
from typing import Annotated
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from fastapi import APIRouter, Depends, HTTPException, status

from auth.spotify_playback_client import SpotifyPlaybackClient, SpotifyPlaybackError
from auth.spotify_session import SpotifySession
from auth.spotify_session import SpotifySessionStore
from providers.spotify import SpotifyProvider
import schemas
from core.dependencies import (
    get_resolver_debug_service,
    get_spotify_playback_client,
    get_spotify_session_store,
)
from services.resolver_debug_service import ResolverDebugService

router = APIRouter()

SpotifySessionStoreDep = Annotated[SpotifySessionStore, Depends(get_spotify_session_store)]
SpotifyPlaybackClientDep = Annotated[SpotifyPlaybackClient, Depends(get_spotify_playback_client)]
ResolverDebugServiceDep = Annotated[ResolverDebugService, Depends(get_resolver_debug_service)]


@router.get("/debug/spotify")
def debug_spotify(
    session_store: SpotifySessionStoreDep,
    playback_client: SpotifyPlaybackClientDep,
) -> dict:
    """Return the current in-memory Spotify auth and device state.

    This endpoint exists for temporary development diagnostics only. It reads
    the existing Spotify session store and uses the concrete playback client to
    inspect available Spotify Connect devices without touching playback,
    queueing, or agent orchestration flows.
    """

    session = session_store.get_session()
    normalized_devices: list[dict[str, object]] = []
    spotify_api_response: dict[str, object] | None = None

    if session is not None:
        try:
            devices = playback_client.get_available_devices()
        except SpotifyPlaybackError:
            devices = []

        session = session_store.get_session() or session
        spotify_api_response = _fetch_raw_spotify_devices(session)

        normalized_devices = [
            {
                "id": device.device_id,
                "name": device.device_name,
                "is_active": device.is_active,
            }
            for device in devices
        ]

    return {
        "connected": session is not None,
        "spotify_enabled": session_store.spotify_enabled,
        "token_present": bool(session and session.access_token),
        "refresh_token_present": bool(session and session.refresh_token),
        "expires_at": session.expires_at.isoformat() if session else None,
        "spotify_api_response": spotify_api_response,
        "normalized_devices": normalized_devices,
    }


@router.get("/debug/spotify/provider")
def debug_spotify_provider() -> dict[str, object]:
    """Verify Spotify provider configuration and client credentials access.

    This endpoint bypasses resolver, playback, and MusicBrainz code paths so
    Spotify catalog access can be validated in isolation during development.
    """

    if not _is_development_mode():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    client_id = os.getenv("SPOTIFY_CLIENT_ID")
    client_secret = os.getenv("SPOTIFY_CLIENT_SECRET")
    redirect_uri = os.getenv("SPOTIFY_REDIRECT_URI")

    provider_initialized = False
    provider_error: str | None = None
    try:
        SpotifyProvider()
        provider_initialized = True
    except Exception as error:  # pragma: no cover - defensive diagnostic path
        provider_error = f"{type(error).__name__}: {error}"

    token_probe = _probe_spotify_client_credentials(
        client_id=client_id,
        client_secret=client_secret,
    )

    return {
        "environment": {
            "spotify_client_id_loaded": bool(client_id),
            "spotify_client_secret_loaded": bool(client_secret),
            "spotify_redirect_uri": redirect_uri,
        },
        "provider_initializes_successfully": provider_initialized,
        "provider_initialization_error": provider_error,
        "client_credentials": token_probe,
    }


@router.get("/debug/spotify/track/{track_id}")
def debug_spotify_track(track_id: str) -> dict[str, object]:
    """Fetch one Spotify track directly through SpotifyProvider only."""

    if not _is_development_mode():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

    provider = SpotifyProvider()
    normalized_track_id = track_id.strip()
    try:
        song = provider.get_song(normalized_track_id)
        return {
            "track_id": normalized_track_id,
            "provider": "spotify",
            "metadata": asdict(song),
            "request_debug": provider.last_request_debug,
            "traceback": None,
        }
    except Exception as error:
        return {
            "track_id": normalized_track_id,
            "provider": "spotify",
            "metadata": None,
            "request_debug": provider.last_request_debug,
            "exception": f"{type(error).__name__}: {error}",
            "traceback": traceback.format_exc(),
        }


@router.get("/rooms/{room_id}/resolver/debug/latest", response_model=schemas.ResolverDebugTrace | None)
def debug_latest_resolver_trace(
    room_id: str,
    resolver_debug_service: ResolverDebugServiceDep,
) -> schemas.ResolverDebugTrace | None:
    """Return the latest room-scoped resolver trace in development mode only."""

    if not _is_development_mode():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return resolver_debug_service.get_latest(room_id)


def _fetch_raw_spotify_devices(session: SpotifySession) -> dict[str, object]:
    """Fetch the raw Spotify devices response for development diagnostics.

    The debug endpoint intentionally exposes the unmodified payload returned by
    Spotify so development-time mismatches between the raw API contract and the
    normalized device model are easy to inspect.
    """

    request = Request(
        SpotifyPlaybackClient.DEVICES_URL,
        headers={"Authorization": f"Bearer {session.access_token}"},
        method="GET",
    )

    try:
        with urlopen(request, timeout=SpotifyPlaybackClient.REQUEST_TIMEOUT_SECONDS) as response:
            payload = response.read().decode("utf-8")
            if not payload:
                return {}
            return json.loads(payload)
    except HTTPError as error:
        return {
            "status_code": error.code,
            "error_message": error.reason,
            "response_body": _read_error_body(error),
        }
    except URLError as error:
        return {
            "status_code": None,
            "error_message": str(error.reason),
            "response_body": None,
        }
    except json.JSONDecodeError:
        return {
            "status_code": None,
            "error_message": "Spotify returned invalid JSON.",
            "response_body": None,
        }


def _probe_spotify_client_credentials(
    *,
    client_id: str | None,
    client_secret: str | None,
) -> dict[str, object]:
    """Request a Spotify client-credentials token and expose the raw outcome."""

    if not client_id:
        return {
            "success": False,
            "http_status": None,
            "token_received": False,
            "expires_in": None,
            "spotify_error_response": None,
            "exception_message": "RuntimeError: SPOTIFY_CLIENT_ID is missing.",
        }
    if not client_secret:
        return {
            "success": False,
            "http_status": None,
            "token_received": False,
            "expires_in": None,
            "spotify_error_response": None,
            "exception_message": "RuntimeError: SPOTIFY_CLIENT_SECRET is missing.",
        }

    basic_token = base64.b64encode(f"{client_id}:{client_secret}".encode("utf-8")).decode("utf-8")
    body = urlencode({"grant_type": "client_credentials"}).encode("utf-8")
    request = Request(
        SpotifyProvider.TOKEN_URL,
        data=body,
        headers={
            "Authorization": f"Basic {basic_token}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=SpotifyProvider.REQUEST_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return {
                "success": True,
                "http_status": response.status,
                "token_received": bool(payload.get("access_token")),
                "expires_in": payload.get("expires_in"),
                "spotify_error_response": None,
                "exception_message": None,
            }
    except HTTPError as error:
        error_body = _read_error_body(error)
        try:
            parsed_error = json.loads(error_body) if error_body else None
        except json.JSONDecodeError:
            parsed_error = error_body
        return {
            "success": False,
            "http_status": error.code,
            "token_received": False,
            "expires_in": None,
            "spotify_error_response": parsed_error,
            "exception_message": f"{type(error).__name__}: {error}",
        }
    except Exception as error:  # pragma: no cover - diagnostic endpoint
        return {
            "success": False,
            "http_status": None,
            "token_received": False,
            "expires_in": None,
            "spotify_error_response": None,
            "exception_message": f"{type(error).__name__}: {error}",
        }


def _read_error_body(error: HTTPError) -> str | None:
    """Safely read the raw response body from a Spotify HTTP error."""

    try:
        payload = error.read()
    except OSError:
        return None
    if not payload:
        return None
    return payload.decode("utf-8", errors="replace")


def _is_development_mode() -> bool:
    """Return whether development-only debug endpoints should be exposed."""

    return os.getenv("PARTYQUEUE_ENV", "development").strip().lower() != "production"
