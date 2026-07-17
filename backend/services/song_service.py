from __future__ import annotations

from sqlalchemy.orm import Session

import models
import schemas
from services.resolver_service import SongResolverService


class SongService:
    """Service responsible for persistence of queue songs."""

    def __init__(self, db: Session, resolver_service: SongResolverService) -> None:
        self.db = db
        self.resolver_service = resolver_service

    def create_song(self, room_id: str, song: schemas.SongCreate) -> models.Song:
        """Resolve a song through the agent layer and persist it in the queue."""
        resolved_result = self.resolver_service.resolve_song_for_queue(song)
        resolved_song = resolved_result.song
        next_position = (
            self.db.query(models.Song)
            .filter(models.Song.room_id == room_id)
            .count()
        )
        db_song = models.Song(
            room_id=room_id,
            position=next_position,
            resolution_confidence=resolved_result.resolution_confidence,
            resolution_reason=resolved_result.resolution_reason,
            **resolved_song.model_dump(),
        )
        self.db.add(db_song)
        self.db.commit()
        self.db.refresh(db_song)
        return db_song
