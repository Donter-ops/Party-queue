from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from decision.decision_types import DecisionStrategy


@dataclass(slots=True)
class AgentDecision:
    """Structured result returned by orchestration agents.

    The decision object is the boundary between orchestration and execution. It
    records which provider, strategy, confidence score, and reasoning chain led
    to the chosen next step. This allows future AI agents, audit tools, and
    observability layers to inspect and compare decisions without changing the
    API or persistence layers.
    """

    provider: str | None
    strategy: DecisionStrategy
    confidence: float
    reasoning: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
