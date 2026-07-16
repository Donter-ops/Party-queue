from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse

from auth.spotify_auth import SpotifyAuthService
from core.dependencies import get_spotify_auth_service

router = APIRouter()

SpotifyAuthServiceDep = Annotated[SpotifyAuthService, Depends(get_spotify_auth_service)]


@router.get("/auth/spotify/login")
def spotify_login(auth_service: SpotifyAuthServiceDep) -> RedirectResponse:
    """Redirect the room host to Spotify's authorization page."""

    return RedirectResponse(url=auth_service.build_login_url(), status_code=status.HTTP_307_TEMPORARY_REDIRECT)


@router.get("/auth/spotify/callback")
def spotify_callback(
    auth_service: SpotifyAuthServiceDep,
    code: Annotated[str | None, Query()] = None,
    state: Annotated[str | None, Query()] = None,
    error: Annotated[str | None, Query()] = None,
) -> RedirectResponse:
    """Handle the Spotify OAuth callback and persist the host session."""

    if error:
        return RedirectResponse(
            url=auth_service.callback_redirect_url(success=False, error=error),
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )

    if not code or not state:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing Spotify OAuth callback parameters.")

    try:
        auth_service.handle_callback(code=code, state=state)
    except ValueError as exc:
        return RedirectResponse(
            url=auth_service.callback_redirect_url(success=False, error=str(exc)),
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )
    except RuntimeError as exc:
        return RedirectResponse(
            url=auth_service.callback_redirect_url(success=False, error=str(exc)),
            status_code=status.HTTP_307_TEMPORARY_REDIRECT,
        )

    return RedirectResponse(
        url=auth_service.callback_redirect_url(success=True),
        status_code=status.HTTP_307_TEMPORARY_REDIRECT,
    )
