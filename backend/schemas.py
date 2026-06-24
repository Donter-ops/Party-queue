from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class SongBase(BaseModel):
    title: str
    artist: str
    added_by: str
    source: str


class SongCreate(SongBase):
    pass


class SongResponse(SongBase):
    id: str
    position: int

    model_config = ConfigDict(from_attributes=True)


class RoomCreate(BaseModel):
    name: str


class RoomResponse(BaseModel):
    id: str
    name: str

    model_config = ConfigDict(from_attributes=True)


class RoomDetailResponse(RoomResponse):
    songs: list[SongResponse]


class SongMoveRequest(BaseModel):
    new_position: int
