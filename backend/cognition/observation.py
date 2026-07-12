from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Observation:
    """Structured snapshot of everything the agent can currently observe.

    This model is the first stage of the cognitive pipeline. It is meant to
    capture raw, structured facts before any reasoning or planning occurs, so
    future AI systems can consume the same consistent input boundary.
    """

    payload_type: str
    source: str | None
    provider_hint: str | None
    has_external_url: bool
    facts: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
