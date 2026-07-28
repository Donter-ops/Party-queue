from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

import schemas
from core.dependencies import get_playback_service
from services.playback_service import PlaybackService

router = APIRouter()

PlaybackServiceDep = Annotated[PlaybackService, Depends(get_playback_service)]


@router.get("/rooms/{room_id}/playback", response_model=schemas.PlaybackSessionResponse | None)
def get_playback_session(
    room_id: str,
    playback_service: PlaybackServiceDep,
) -> schemas.PlaybackSessionResponse | None:
    """Return the current playback session for the room when one exists."""

    return playback_service.get_session(room_id)


@router.post("/rooms/{room_id}/playback/start", response_model=schemas.PlaybackSessionResponse)
def start_playback(
    room_id: str,
    playback_service: PlaybackServiceDep,
) -> schemas.PlaybackSessionResponse:
    """Start playback for the room queue."""

    return playback_service.start(room_id)


@router.post("/rooms/{room_id}/playback/pause", response_model=schemas.PlaybackSessionResponse)
def pause_playback(
    room_id: str,
    playback_service: PlaybackServiceDep,
) -> schemas.PlaybackSessionResponse:
    """Pause the current playback session."""

    return playback_service.pause(room_id)


@router.post("/rooms/{room_id}/playback/resume", response_model=schemas.PlaybackSessionResponse)
def resume_playback(
    room_id: str,
    playback_service: PlaybackServiceDep,
) -> schemas.PlaybackSessionResponse:
    """Resume playback for the room."""

    return playback_service.resume(room_id)


@router.post("/rooms/{room_id}/playback/finish", response_model=schemas.PlaybackSessionResponse)
def finish_playback(
    room_id: str,
    playback_service: PlaybackServiceDep,
) -> schemas.PlaybackSessionResponse:
    """Advance playback after the current item finishes."""

    return playback_service.finish(room_id)


@router.post("/rooms/{room_id}/playback/next", response_model=schemas.PlaybackSessionResponse)
def next_playback(
    room_id: str,
    playback_service: PlaybackServiceDep,
) -> schemas.PlaybackSessionResponse:
    """Advance playback to the next queued item."""

    return playback_service.next(room_id)


@router.post("/rooms/{room_id}/playback/previous", response_model=schemas.PlaybackSessionResponse)
def previous_playback(
    room_id: str,
    playback_service: PlaybackServiceDep,
) -> schemas.PlaybackSessionResponse:
    """Return playback to the previous song when history exists."""

    return playback_service.previous(room_id)
