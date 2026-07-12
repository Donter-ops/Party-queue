from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, selectinload

import models
import schemas


class QueueService:
    """Service responsible for room and queue mutation workflows."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def create_room(self, room: schemas.RoomCreate) -> models.Room:
        db_room = models.Room(name=room.name)
        self.db.add(db_room)
        self.db.commit()
        self.db.refresh(db_room)
        return db_room

    def get_room(self, room_id: str) -> models.Room | None:
        return (
            self.db.query(models.Room)
            .options(selectinload(models.Room.songs))
            .filter(models.Room.id == room_id)
            .first()
        )

    def require_room(self, room_id: str) -> models.Room:
        room = self.get_room(room_id)
        if room is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
        return room

    def get_song(self, room_id: str, song_id: str) -> models.Song | None:
        return (
            self.db.query(models.Song)
            .filter(models.Song.room_id == room_id, models.Song.id == song_id)
            .first()
        )

    def list_songs(self, room_id: str) -> list[models.Song]:
        """Return all room songs ordered by queue position."""

        return (
            self.db.query(models.Song)
            .filter(models.Song.room_id == room_id)
            .order_by(models.Song.position.asc())
            .all()
        )

    def get_next_song(self, room_id: str, current_position: int | None) -> models.Song | None:
        """Return the next queued song after the provided position.

        A ``None`` position is treated as a request for the first queue entry,
        which keeps the method useful for both session bootstrap and forward
        playback transitions.
        """

        songs = self.list_songs(room_id)
        if not songs:
            return None

        if current_position is None:
            return songs[0]

        return next(
            (song for song in songs if song.position > current_position),
            None,
        )

    def delete_song(self, room_id: str, song_id: str) -> None:
        db_song = self.get_song(room_id=room_id, song_id=song_id)
        if db_song is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Song not found")

        deleted_position = db_song.position
        self.db.delete(db_song)

        remaining_songs = (
            self.db.query(models.Song)
            .filter(
                models.Song.room_id == room_id,
                models.Song.position > deleted_position,
            )
            .order_by(models.Song.position.asc())
            .all()
        )
        for song in remaining_songs:
            song.position -= 1

        self.db.commit()

    def move_song(
        self,
        room_id: str,
        song_id: str,
        move_request: schemas.SongMoveRequest,
    ) -> models.Song:
        songs = self.list_songs(room_id)

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

        self.db.commit()
        self.db.refresh(moved_song)
        return moved_song
