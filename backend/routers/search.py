from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from core.dependencies import get_input_resolver_service
from schemas.search import SearchResultResponse
from services.input_resolver import InputResolverService

router = APIRouter()

InputResolverDep = Annotated[InputResolverService, Depends(get_input_resolver_service)]


@router.get("/search", response_model=list[SearchResultResponse])
def search_songs(
    input_resolver_service: InputResolverDep,
    input: Annotated[str | None, Query(min_length=1, description="Universal song input")] = None,
    q: Annotated[str | None, Query(min_length=1, description="Backward compatible search query")] = None,
) -> list[SearchResultResponse]:
    """Expose the universal song input pipeline through the search API."""

    effective_input = (input or q or "").strip()
    return [
        song.to_response()
        for song in input_resolver_service.resolve(effective_input)
    ]
