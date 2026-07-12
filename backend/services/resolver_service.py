from __future__ import annotations

import schemas
from agents.orchestrator_agent import OrchestratorAgent
from decision.decision import AgentDecision


class SongResolverService:
    """Service wrapper around the orchestration layer for song preparation.

    The resolver is the compatibility boundary between today's synchronous song
    creation flow and tomorrow's richer decision-driven agent workflows.
    """

    def __init__(self, orchestrator_agent: OrchestratorAgent) -> None:
        self.orchestrator_agent = orchestrator_agent

    def resolve_song(self, song: schemas.SongCreate) -> schemas.SongCreate:
        """Delegate song preparation to the orchestrator agent.

        The orchestrator now returns a decision object. Current functionality is
        preserved by keeping the original song payload unchanged after the
        decision has been recorded.
        """
        _decision = self.decide_song(song)
        return song

    def decide_song(self, song: schemas.SongCreate) -> AgentDecision:
        """Return the structured orchestration decision for the incoming song."""
        return self.orchestrator_agent.decide(song)
