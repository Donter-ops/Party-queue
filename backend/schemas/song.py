from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class SongBase(BaseModel):
    title: str
    artist: str
    added_by: str
    source: str
    external_url: str | None = None


class SongCreate(SongBase):
    pass


class SongResponse(SongBase):
    id: str
    position: int

    model_config = ConfigDict(from_attributes=True)


class SongMoveRequest(BaseModel):
    new_position: int
