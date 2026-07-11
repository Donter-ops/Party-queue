from __future__ import annotations

from sqlalchemy.orm import Session

import models
import schemas
from services.queue_service import QueueService
from services.resolver_service import SongResolverService
from services.song_service import SongService


def create_room(db: Session, room: schemas.RoomCreate) -> models.Room:
    return QueueService(db).create_room(room)


def get_room(db: Session, room_id: str) -> models.Room | None:
    return QueueService(db).get_room(room_id)


def create_song(db: Session, room_id: str, song: schemas.SongCreate) -> models.Song:
    return SongService(db=db, resolver_service=SongResolverService()).create_song(room_id, song)


def get_song(db: Session, room_id: str, song_id: str) -> models.Song | None:
    return QueueService(db).get_song(room_id=room_id, song_id=song_id)


def delete_song(db: Session, room_id: str, song_id: str) -> None:
    QueueService(db).delete_song(room_id=room_id, song_id=song_id)


def move_song(
    db: Session,
    room_id: str,
    song_id: str,
    move_request: schemas.SongMoveRequest,
) -> models.Song:
    return QueueService(db).move_song(
        room_id=room_id,
        song_id=song_id,
        move_request=move_request,
    )
