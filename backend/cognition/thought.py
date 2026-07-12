from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Thought:
    """Structured analysis derived from an observation.

    A thought is the agent's deterministic interpretation of the observed
    facts. It intentionally separates analysis from planning so future AI
    models can improve reasoning quality without changing tool execution APIs.
    """

    summary: str
    provider: str | None
    strategy_hint: str
    reasoning: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
