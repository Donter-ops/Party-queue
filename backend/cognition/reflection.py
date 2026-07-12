from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class Reflection:
    """Post-decision evaluation emitted by the cognitive pipeline.

    Reflection provides a structured place to assess whether a decision appears
    successful. It is intentionally lightweight today so future AI evaluators
    can extend it without changing upstream route or service behavior.
    """

    success: bool
    summary: str
    notes: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
