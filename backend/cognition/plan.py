from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class ExecutionPlan:
    """Ordered plan describing which tools the agent intends to execute.

    The plan is deterministic today, but it creates a stable boundary for
    future multi-step or multi-agent workflows where planning and execution
    may diverge or be revised.
    """

    tool_names: list[str] = field(default_factory=list)
    steps: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
