from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from core.database import get_db
from services.queue_service import QueueService
from services.resolver_service import SongResolverService
from services.song_service import SongService

DbSession = Annotated[Session, Depends(get_db)]


def get_song_resolver_service() -> SongResolverService:
    return SongResolverService()


def get_queue_service(db: DbSession) -> QueueService:
    return QueueService(db)


def get_song_service(
    db: DbSession,
    resolver_service: Annotated[SongResolverService, Depends(get_song_resolver_service)],
) -> SongService:
    return SongService(db=db, resolver_service=resolver_service)
