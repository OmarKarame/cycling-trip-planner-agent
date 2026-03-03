from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SessionState:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    messages: list[dict[str, Any]] = field(default_factory=list)
    route_fetched: bool = False
    accommodation_fetched: bool = False
    weather_fetched: bool = False
    elevation_fetched: bool = False
    tools_used_this_turn: list[str] = field(default_factory=list)


class SessionStore:
    """In-memory session storage keyed by session ID."""

    def __init__(self) -> None:
        self._sessions: dict[str, SessionState] = {}

    def get_or_create(self, session_id: str | None = None) -> SessionState:
        """Return an existing session or create a new one."""
        if session_id and session_id in self._sessions:
            return self._sessions[session_id]
        state = SessionState()
        self._sessions[state.session_id] = state
        return state

    def get(self, session_id: str) -> SessionState | None:
        return self._sessions.get(session_id)
