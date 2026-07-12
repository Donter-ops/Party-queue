from __future__ import annotations

from typing import Any

import schemas
from agents.base_agent import BaseAgent
from cognition.observation import Observation
from cognition.plan import ExecutionPlan
from cognition.reflection import Reflection
from cognition.thought import Thought
from decision.confidence import ConfidenceHelper
from decision.decision import AgentDecision
from decision.decision_types import DecisionStrategy
from tools.base_tool import BaseTool
from tools.metadata_tool import MetadataTool
from tools.queue_tool import QueueTool
from tools.search_tool import SearchTool
from tools.search_models import SearchRequest, SearchResult


class OrchestratorAgent(BaseAgent):
    """Coordinates song-related workflows by selecting the right backend tool.

    This agent deliberately contains no AI or LLM logic yet. Its responsibility
    is to move through a deterministic cognitive pipeline: observe, think, plan,
    execute, and reflect. The output remains structured so future AI models can
    replace the deterministic reasoning without changing the surrounding system.
    """

    def __init__(
        self,
        queue_tool: QueueTool,
        metadata_tool: MetadataTool,
        search_tool: SearchTool,
        confidence_helper: ConfidenceHelper,
    ) -> None:
        self.queue_tool = queue_tool
        self.metadata_tool = metadata_tool
        self.search_tool = search_tool
        self.confidence_helper = confidence_helper

    def decide(self, payload: Any) -> AgentDecision:
        """Run the full cognitive pipeline and return the resulting decision."""
        observation = self.observe(payload)
        thought = self.think(observation)
        plan = self.plan(thought)
        decision = self.execute(plan)
        self.reflect(decision)
        return decision

    def search(self, request: SearchRequest) -> SearchResult:
        """Execute the deterministic search flow through the cognitive pipeline.

        This method gives services a direct, typed way to use the agent for
        search orchestration while keeping the same internal observe-think-plan-
        execute-reflect sequence that future AI-backed agent behavior will use.
        """

        observation = self.observe(request)
        thought = self.think(observation)
        plan = self.plan(thought)
        result = self.execute_search(plan)
        self.reflect_search(result)
        return result

    def observe(self, payload: Any) -> Observation:
        """Collect all currently available facts about the incoming payload."""
        if isinstance(payload, SearchRequest):
            normalized_query = payload.query.strip()
            facts = [
                f"Search query received: '{normalized_query}'.",
                f"Target provider is '{payload.provider}'.",
                f"Requested result limit is {payload.limit}.",
            ]
            return Observation(
                payload_type=type(payload).__name__,
                source=payload.provider,
                provider_hint=payload.provider,
                has_external_url=False,
                facts=facts,
                metadata={"payload": payload},
            )

        if isinstance(payload, schemas.SongCreate):
            provider_hint = payload.source if payload.source != "manual" else None
            facts = [
                f"Song source is '{payload.source}'.",
                f"External URL present: {bool(payload.external_url)}.",
            ]
            return Observation(
                payload_type=type(payload).__name__,
                source=payload.source,
                provider_hint=provider_hint,
                has_external_url=bool(payload.external_url),
                facts=facts,
                metadata={"payload": payload},
            )
        return super().observe(payload)

    def think(self, observation: Observation) -> Thought:
        """Analyze the observation and derive a deterministic thought."""
        search_payload: SearchRequest | None = None
        if isinstance(observation.metadata.get("payload"), SearchRequest):
            search_payload = observation.metadata["payload"]
            return Thought(
                summary="Search request should be executed through SearchTool.",
                provider=search_payload.provider,
                strategy_hint=DecisionStrategy.SEARCH_EQUIVALENT.value,
                reasoning=[
                    *observation.facts,
                    "SearchRequest payload detected.",
                ],
                metadata={
                    "observation": observation,
                    "search_request": search_payload,
                },
            )

        provider = observation.provider_hint
        payload: schemas.SongCreate | None = observation.metadata.get("payload")
        search_query = None
        if payload is not None:
            search_query = f"{payload.artist} {payload.title}".strip()

        if observation.source == "manual":
            strategy_hint = DecisionStrategy.SEARCH_EQUIVALENT.value
            summary = "Manual source requires equivalent-source lookup later."
        elif provider is not None:
            strategy_hint = DecisionStrategy.DIRECT_PLAYBACK.value
            summary = f"{provider} source can be treated as a direct provider signal."
        else:
            strategy_hint = DecisionStrategy.REQUEST_USER_INPUT.value
            summary = "Unknown source requires additional clarification."

        reasoning = list(observation.facts)
        if provider:
            reasoning.append(f"Provider hint '{provider}' extracted from source.")
        else:
            reasoning.append("No provider hint extracted from source.")

        return Thought(
            summary=summary,
            provider=provider,
            strategy_hint=strategy_hint,
            reasoning=reasoning,
            metadata={
                "observation": observation,
                "search_request": SearchRequest(
                    query=search_query or "",
                    provider="local",
                    limit=5,
                    source_hint=observation.source,
                ),
            },
        )

    def plan(self, thought: Thought) -> ExecutionPlan:
        """Generate an execution plan that describes which tools will be used."""
        tool = self._select_tool_from_thought(thought)
        search_request: SearchRequest = thought.metadata["search_request"]
        return ExecutionPlan(
            tool_names=[tool.__class__.__name__],
            steps=[
                f"Execute {tool.__class__.__name__}",
                "Convert execution result into AgentDecision",
            ],
            metadata={
                "thought": thought,
                "tool": tool,
                "search_request": search_request,
            },
        )

    def execute(self, plan: ExecutionPlan) -> AgentDecision:
        """Execute the plan and return a structured decision."""
        thought = plan.metadata["thought"]
        observation = thought.metadata["observation"]
        payload = observation.metadata["payload"]
        tool: BaseTool = plan.metadata["tool"]
        search_request: SearchRequest = plan.metadata["search_request"]
        tool_result = tool.run(search_request)
        return self._build_decision(
            payload=payload,
            observation=observation,
            thought=thought,
            tool=tool,
            tool_result=tool_result,
        )

    def execute_search(self, plan: ExecutionPlan) -> SearchResult:
        """Execute a plan specifically for search and return typed results."""

        tool: BaseTool = plan.metadata["tool"]
        search_request: SearchRequest = plan.metadata["search_request"]
        tool_result = tool.run(search_request)
        if not isinstance(tool_result, SearchResult):
            raise TypeError("Search execution must return SearchResult.")
        return tool_result

    def reflect(self, decision: AgentDecision) -> Reflection:
        """Evaluate whether the emitted decision appears internally consistent."""
        success = decision.strategy != DecisionStrategy.NO_PLAYABLE_SOURCE
        notes = [
            f"Decision emitted with confidence {decision.confidence:.2f}.",
            f"Strategy chosen: {decision.strategy.value}.",
        ]
        return Reflection(
            success=success,
            summary="Deterministic reflection completed.",
            notes=notes,
            metadata={"decision": decision},
        )

    def reflect_search(self, result: SearchResult) -> Reflection:
        """Evaluate whether a search execution produced usable results."""

        return Reflection(
            success=result.total_matches > 0,
            summary="Deterministic search reflection completed.",
            notes=[
                f"Search provider: {result.provider}.",
                f"Search returned {result.total_matches} matches.",
                f"Search confidence: {result.confidence:.2f}.",
            ],
            metadata={"search_result": result},
        )

    def _build_decision(
        self,
        *,
        payload: Any,
        observation: Observation,
        thought: Thought,
        tool: BaseTool,
        tool_result: Any,
    ) -> AgentDecision:
        """Translate deterministic routing state into an `AgentDecision`."""
        if isinstance(payload, schemas.SongCreate):
            provider = thought.provider
            reasoning = self._build_reasoning(observation, thought, tool)
            strategy = DecisionStrategy(thought.strategy_hint)
            search_result = tool_result if isinstance(tool_result, SearchResult) else None
            confidence = self.confidence_helper.calculate(
                matched_provider=provider is not None,
                has_external_url=bool(payload.external_url),
                search_match_count=search_result.total_matches if search_result else 0,
            )
            return AgentDecision(
                provider=provider,
                strategy=strategy,
                confidence=confidence,
                reasoning=reasoning,
                metadata={
                    "tool": tool.__class__.__name__,
                    "source": payload.source,
                    "external_url_present": bool(payload.external_url),
                    "tool_result_type": type(tool_result).__name__,
                    "observation_payload_type": observation.payload_type,
                    "thought_summary": thought.summary,
                    "search_result": self._serialize_search_result(search_result),
                },
            )

        return AgentDecision(
            provider=None,
            strategy=DecisionStrategy.NO_PLAYABLE_SOURCE,
            confidence=0.0,
            reasoning=["Unsupported payload type for orchestrator decision."],
            metadata={
                "tool": tool.__class__.__name__,
                "payload_type": type(payload).__name__,
            },
        )

    def _build_reasoning(
        self,
        observation: Observation,
        thought: Thought,
        tool: BaseTool,
    ) -> list[str]:
        """Return deterministic reasoning by combining cognitive stages."""
        return [
            *observation.facts,
            thought.summary,
            f"{tool.__class__.__name__} selected for execution.",
        ]

    def _select_tool_from_thought(self, thought: Thought) -> BaseTool:
        """Choose the tool that should execute the current thought.

        SearchTool is now the first functional tool in the architecture and is
        used to gather deterministic local catalog evidence for the decision.
        """
        return self.search_tool

    def _serialize_search_result(self, result: SearchResult | None) -> dict[str, Any] | None:
        """Convert a search result into metadata-safe primitives."""
        if result is None:
            return None

        return {
            "query": result.query,
            "provider": result.provider,
            "total_matches": result.total_matches,
            "confidence": result.confidence,
            "matches": [
                {
                    "provider": match.provider,
                    "provider_id": match.provider_id,
                    "title": match.title,
                    "artist": match.artist,
                    "external_url": match.external_url,
                }
                for match in result.matches
            ],
        }
