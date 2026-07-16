from __future__ import annotations

from urllib.parse import urlencode

from auth.spotify_session import SpotifySession, SpotifySessionStore
from auth.spotify_tokens import SpotifyOAuthConfig, SpotifyTokenService


class SpotifyAuthService:
    """High-level Spotify OAuth flow coordinator.

    The service owns login URL creation, callback validation, and host session
    storage. It exposes a narrow interface to the router so the HTTP layer does
    not need to know how Spotify OAuth or token exchange works internally.
    """

    AUTHORIZE_URL = "https://accounts.spotify.com/authorize"

    def __init__(
        self,
        config: SpotifyOAuthConfig,
        token_service: SpotifyTokenService,
        session_store: SpotifySessionStore,
    ) -> None:
        self.config = config
        self.token_service = token_service
        self.session_store = session_store

    def build_login_url(self) -> str:
        """Return the Spotify authorization URL for the host."""

        state = self.session_store.create_state()
        query = urlencode(
            {
                "client_id": self.config.client_id,
                "response_type": "code",
                "redirect_uri": self.config.redirect_uri,
                "state": state,
                "scope": self.config.scope,
                "show_dialog": "true",
            }
        )
        return f"{self.AUTHORIZE_URL}?{query}"

    def handle_callback(self, code: str, state: str) -> SpotifySession:
        """Validate the callback state and exchange the code for tokens."""

        if not self.session_store.consume_state(state):
            raise ValueError("Invalid or expired Spotify OAuth state.")

        session = self.token_service.exchange_code(code)
        return self.session_store.set_session(session)

    def callback_redirect_url(self, *, success: bool, error: str | None = None) -> str:
        """Return the frontend URL to open after OAuth completes."""

        params = {"status": "success" if success else "error"}
        if error:
            params["error"] = error
        return f"{self.config.frontend_redirect_uri}?{urlencode(params)}"
