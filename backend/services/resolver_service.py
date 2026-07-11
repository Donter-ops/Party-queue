from __future__ import annotations

import schemas


class SongResolverService:
    def resolve_song(self, song: schemas.SongCreate) -> schemas.SongCreate:
        return song
