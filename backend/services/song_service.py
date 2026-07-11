from __future__ import annotations

from sqlalchemy.orm import Session

import models
import schemas
from services.resolver_service import SongResolverService


class SongService:
    def __init__(self, db: Session, resolver_service: SongResolverService) -> None:
        self.db = db
        self.resolver_service = resolver_service

    def create_song(self, room_id: str, song: schemas.SongCreate) -> models.Song:
        resolved_song = self.resolver_service.resolve_song(song)
        next_position = (
            self.db.query(models.Song)
            .filter(models.Song.room_id == room_id)
            .count()
        )
        db_song = models.Song(
            room_id=room_id,
            position=next_position,
            **resolved_song.model_dump(),
        )
        self.db.add(db_song)
        self.db.commit()
        self.db.refresh(db_song)
        return db_song
