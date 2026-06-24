from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, selectinload

import models
import schemas


def create_room(db: Session, room: schemas.RoomCreate) -> models.Room:
    db_room = models.Room(name=room.name)
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return db_room


def get_room(db: Session, room_id: str) -> models.Room | None:
    return (
        db.query(models.Room)
        .options(selectinload(models.Room.songs))
        .filter(models.Room.id == room_id)
        .first()
    )


def create_song(db: Session, room_id: str, song: schemas.SongCreate) -> models.Song:
    next_position = (
        db.query(models.Song)
        .filter(models.Song.room_id == room_id)
        .count()
    )
    db_song = models.Song(
        room_id=room_id,
        position=next_position,
        **song.model_dump(),
    )
    db.add(db_song)
    db.commit()
    db.refresh(db_song)
    return db_song


def get_song(db: Session, room_id: str, song_id: str) -> models.Song | None:
    return (
        db.query(models.Song)
        .filter(models.Song.room_id == room_id, models.Song.id == song_id)
        .first()
    )


def delete_song(db: Session, room_id: str, song_id: str) -> None:
    db_song = get_song(db=db, room_id=room_id, song_id=song_id)
    if db_song is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")

    deleted_position = db_song.position
    db.delete(db_song)

    remaining_songs = (
        db.query(models.Song)
        .filter(
            models.Song.room_id == room_id,
            models.Song.position > deleted_position,
        )
        .order_by(models.Song.position.asc())
        .all()
    )
    for song in remaining_songs:
        song.position -= 1

    db.commit()


def move_song(
    db: Session,
    room_id: str,
    song_id: str,
    move_request: schemas.SongMoveRequest,
) -> models.Song:
    songs = (
        db.query(models.Song)
        .filter(models.Song.room_id == room_id)
        .order_by(models.Song.position.asc())
        .all()
    )

    current_index = next((index for index, song in enumerate(songs) if song.id == song_id), None)
    if current_index is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")

    new_position = move_request.new_position
    if new_position < 0 or new_position >= len(songs):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="new_position is out of range",
        )

    moved_song = songs.pop(current_index)
    songs.insert(new_position, moved_song)

    for index, song in enumerate(songs):
        song.position = index

    db.commit()
    db.refresh(moved_song)
    return moved_song
