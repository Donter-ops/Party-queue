from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

import schemas
from core.dependencies import get_queue_service, get_song_service
from services.queue_service import QueueService
from services.song_service import SongService

router = APIRouter()

QueueServiceDep = Annotated[QueueService, Depends(get_queue_service)]
SongServiceDep = Annotated[SongService, Depends(get_song_service)]


@router.post("/rooms", response_model=schemas.RoomResponse, status_code=status.HTTP_201_CREATED)
def create_room(
    room: schemas.RoomCreate,
    queue_service: QueueServiceDep,
) -> schemas.RoomResponse:
    return queue_service.create_room(room)


@router.get("/rooms/{room_id}", response_model=schemas.RoomDetailResponse)
def read_room(
    room_id: str,
    queue_service: QueueServiceDep,
) -> schemas.RoomDetailResponse:
    return queue_service.require_room(room_id)


@router.post(
    "/rooms/{room_id}/songs",
    response_model=schemas.SongResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_song_for_room(
    room_id: str,
    song: schemas.SongCreate,
    queue_service: QueueServiceDep,
    song_service: SongServiceDep,
) -> schemas.SongResponse:
    queue_service.require_room(room_id)
    return song_service.create_song(room_id=room_id, song=song)


@router.delete("/rooms/{room_id}/songs/{song_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_song_from_room(
    room_id: str,
    song_id: str,
    queue_service: QueueServiceDep,
) -> None:
    queue_service.require_room(room_id)
    queue_service.delete_song(room_id=room_id, song_id=song_id)


@router.put("/rooms/{room_id}/songs/{song_id}/move", response_model=schemas.SongResponse)
def move_song_in_room(
    room_id: str,
    song_id: str,
    move_request: schemas.SongMoveRequest,
    queue_service: QueueServiceDep,
) -> schemas.SongResponse:
    queue_service.require_room(room_id)
    return queue_service.move_song(
        room_id=room_id,
        song_id=song_id,
        move_request=move_request,
    )
