from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from schemas.song import SongResponse


class RoomCreate(BaseModel):
    name: str


class RoomResponse(BaseModel):
    id: str
    name: str

    model_config = ConfigDict(from_attributes=True)


class RoomDetailResponse(RoomResponse):
    songs: list[SongResponse]
