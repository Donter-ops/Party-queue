from __future__ import annotations

from pydantic import BaseModel


class SearchResultResponse(BaseModel):
    """API-safe representation of one search candidate.

    The response model intentionally exposes only the fields the frontend needs
    to render and select a candidate. Provider-native identifiers and richer
    metadata can be added later without changing the initial search flow.
    """

    title: str
    artist: str
    provider: str
    confidence: float
    external_id: str
    external_url: str | None = None
