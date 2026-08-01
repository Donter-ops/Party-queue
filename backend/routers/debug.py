from __future__ import annotations

import os
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

import schemas
from core.dependencies import get_resolver_debug_service
from services.resolver_debug_service import ResolverDebugService

router = APIRouter()

ResolverDebugServiceDep = Annotated[ResolverDebugService, Depends(get_resolver_debug_service)]


@router.get("/rooms/{room_id}/resolver/debug/latest", response_model=schemas.ResolverDebugTrace | None)
def debug_latest_resolver_trace(
    room_id: str,
    resolver_debug_service: ResolverDebugServiceDep,
) -> schemas.ResolverDebugTrace | None:
    """Return the latest room-scoped resolver trace in development mode only."""

    if not _is_development_mode():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return resolver_debug_service.get_latest(room_id)


def _is_development_mode() -> bool:
    """Return whether development-only debug endpoints should be exposed."""

    return os.getenv("PARTYQUEUE_ENV", "development").strip().lower() != "production"
