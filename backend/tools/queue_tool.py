from __future__ import annotations

import schemas
from tools.base_tool import BaseTool


class QueueTool(BaseTool):
    """Tool responsible for queue-safe song preparation.

    The current implementation is intentionally a no-op so existing song
    creation keeps working exactly as before while the orchestration layer is
    introduced.
    """

    def run(self, payload: schemas.SongCreate) -> schemas.SongCreate:
        """Return the incoming song unchanged."""
        return payload
