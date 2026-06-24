from __future__ import annotations

from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

import crud
import schemas
from database import get_db, init_db

init_db()

app = FastAPI(title="PartyQueue API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DbSession = Annotated[Session, Depends(get_db)]


@app.post("/rooms", response_model=schemas.RoomResponse, status_code=status.HTTP_201_CREATED)
def create_room(room: schemas.RoomCreate, db: DbSession) -> schemas.RoomResponse:
    return crud.create_room(db=db, room=room)


@app.get("/rooms/{room_id}", response_model=schemas.RoomDetailResponse)
def read_room(room_id: str, db: DbSession) -> schemas.RoomDetailResponse:
    db_room = crud.get_room(db=db, room_id=room_id)
    if db_room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    return db_room


@app.post(
    "/rooms/{room_id}/songs",
    response_model=schemas.SongResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_song_for_room(
    room_id: str,
    song: schemas.SongCreate,
    db: DbSession,
) -> schemas.SongResponse:
    db_room = crud.get_room(db=db, room_id=room_id)
    if db_room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    return crud.create_song(db=db, room_id=room_id, song=song)


@app.delete("/rooms/{room_id}/songs/{song_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_song_from_room(room_id: str, song_id: str, db: DbSession) -> None:
    db_room = crud.get_room(db=db, room_id=room_id)
    if db_room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    crud.delete_song(db=db, room_id=room_id, song_id=song_id)


@app.put("/rooms/{room_id}/songs/{song_id}/move", response_model=schemas.SongResponse)
def move_song_in_room(
    room_id: str,
    song_id: str,
    move_request: schemas.SongMoveRequest,
    db: DbSession,
) -> schemas.SongResponse:
    db_room = crud.get_room(db=db, room_id=room_id)
    if db_room is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Room not found")
    return crud.move_song(
        db=db,
        room_id=room_id,
        song_id=song_id,
        move_request=move_request,
    )
