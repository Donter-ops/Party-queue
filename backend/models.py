from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    songs: Mapped[list["Song"]] = relationship(
        back_populates="room",
        cascade="all, delete-orphan",
        order_by="Song.position",
    )


class Song(Base):
    __tablename__ = "songs"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    title: Mapped[str] = mapped_column(String, nullable=False)
    artist: Mapped[str] = mapped_column(String, nullable=False)
    added_by: Mapped[str] = mapped_column(String, nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    position: Mapped[int] = mapped_column(nullable=False)
    room_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=False,
    )

    room: Mapped[Room] = relationship(back_populates="songs")
