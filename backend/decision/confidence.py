from __future__ import annotations


class ConfidenceHelper:
    """Utility for producing normalized confidence scores for decisions.

    The helper currently uses deterministic inputs only and returns a float in
    the inclusive range `[0.0, 1.0]`. This creates a stable contract now while
    leaving room for future learned or probabilistic scoring approaches.
    """

    def calculate(
        self,
        *,
        matched_provider: bool,
        has_external_url: bool,
        search_match_count: int = 0,
    ) -> float:
        """Return a simple confidence score based on deterministic rule inputs."""
        if matched_provider and has_external_url:
            return 1.0
        if search_match_count >= 3:
            return 0.9
        if search_match_count > 0:
            return 0.75
        if matched_provider:
            return 0.85
        if has_external_url:
            return 0.65
        return 0.5
