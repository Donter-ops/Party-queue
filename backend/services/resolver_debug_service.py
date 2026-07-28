from __future__ import annotations

import copy

import schemas


class ResolverDebugService:
    """In-memory store for the latest room-scoped resolver trace.

    Resolver traces are development diagnostics, not business data. They stay
    outside the persistence layer so the existing queue and playback schemas do
    not change while developers can still inspect the last cross-provider
    decision per room.
    """

    def __init__(self) -> None:
        self._latest_traces: dict[str, schemas.ResolverDebugTrace] = {}

    def save_latest(self, room_id: str, trace: schemas.ResolverDebugTrace | None) -> None:
        """Store the latest trace for a room when one exists."""

        if trace is None:
            return
        self._latest_traces[room_id] = trace.model_copy(deep=True, update={"room_id": room_id})

    def get_latest(self, room_id: str) -> schemas.ResolverDebugTrace | None:
        """Return the latest stored trace for a room."""

        trace = self._latest_traces.get(room_id)
        if trace is None:
            return None
        return copy.deepcopy(trace)
