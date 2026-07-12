from __future__ import annotations

from providers.base import MusicProvider, ProviderSong
from tools.base_tool import BaseTool


class MetadataTool(BaseTool):
    """Tool responsible for provider-backed metadata resolution workflows."""

    def __init__(self, providers: dict[str, MusicProvider]) -> None:
        self.providers = providers

    def run(self, payload: tuple[str, str, str]) -> ProviderSong:
        """Resolve metadata from a provider using a typed tuple payload.

        Payload format:
        `(provider_name, operation, value)` where operation is `resolve` or
        `get_song`.
        """
        provider_name, operation, value = payload
        provider = self.providers[provider_name]
        if operation == "resolve":
            return provider.resolve(value)
        if operation == "get_song":
            return provider.get_song(value)
        raise ValueError(f"Unsupported metadata operation: {operation}")
