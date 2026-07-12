from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from core.dependencies import get_search_service
from schemas.search import SearchResultResponse
from services.search_service import SearchService

router = APIRouter()

SearchServiceDep = Annotated[SearchService, Depends(get_search_service)]


@router.get("/search", response_model=list[SearchResultResponse])
def search_songs(
    q: Annotated[str, Query(min_length=1, description="User search query")],
    search_service: SearchServiceDep,
) -> list[SearchResultResponse]:
    """Expose provider-backed search results through the backend API."""

    result = search_service.search(q)
    return [
        SearchResultResponse(
            title=match.title,
            artist=match.artist,
            provider=match.provider,
            confidence=match.confidence if match.confidence is not None else result.confidence,
            external_id=match.provider_id,
            external_url=match.external_url,
        )
        for match in result.matches
    ]
