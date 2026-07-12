from __future__ import annotations

from abc import ABC
from typing import Any

from cognition.observation import Observation
from cognition.plan import ExecutionPlan
from cognition.reflection import Reflection
from cognition.thought import Thought
from decision.decision import AgentDecision


class BaseAgent(ABC):
    """Base contract for backend agents that coordinate higher-level workflows.

    The methods are intentionally lightweight placeholders so the project can grow
    into an AI-first architecture later without changing the public agent shape.
    """

    def observe(self, payload: Any) -> Observation:
        """Collect raw facts about the current payload."""
        return Observation(
            payload_type=type(payload).__name__,
            source=None,
            provider_hint=None,
            has_external_url=False,
        )

    def think(self, observation: Observation) -> Thought:
        """Analyze an observation and produce a structured thought."""
        return Thought(
            summary=f"Received observation for {observation.payload_type}.",
            provider=observation.provider_hint,
            strategy_hint="NO_PLAYABLE_SOURCE",
        )

    def plan(self, thought: Thought) -> ExecutionPlan:
        """Generate an execution plan from the current thought."""
        return ExecutionPlan(tool_names=[], steps=["no-op"])

    def execute(self, plan: ExecutionPlan) -> AgentDecision:
        """Execute a previously generated plan and return an agent decision."""
        raise NotImplementedError

    def reflect(self, decision: AgentDecision) -> Reflection:
        """Evaluate whether the emitted decision appears successful."""
        return Reflection(
            success=decision.confidence > 0,
            summary="Default reflection completed.",
        )
