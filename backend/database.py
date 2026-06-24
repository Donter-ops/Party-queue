from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./partyqueue.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    class_=Session,
)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    import models

    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    song_columns = {column["name"] for column in inspector.get_columns("songs")}

    if "songs" in inspector.get_table_names() and "position" not in song_columns:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE songs ADD COLUMN position INTEGER NOT NULL DEFAULT 0"
                )
            )

        db = SessionLocal()
        try:
            songs = (
                db.query(models.Song)
                .order_by(models.Song.room_id.asc(), models.Song.id.asc())
                .all()
            )

            next_positions: dict[str, int] = {}
            for song in songs:
                song.position = next_positions.get(song.room_id, 0)
                next_positions[song.room_id] = song.position + 1

            db.commit()
        finally:
            db.close()
