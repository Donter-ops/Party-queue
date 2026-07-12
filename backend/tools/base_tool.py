from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseTool(ABC):
    """Abstract base class for backend tools used by orchestration agents.

    Each tool owns exactly one responsibility so future agents can compose them
    without coupling orchestration logic to providers or persistence concerns.
    """

    @abstractmethod
    def run(self, payload: Any) -> Any:
        """Execute the tool's single responsibility for the given payload."""
        raise NotImplementedError
