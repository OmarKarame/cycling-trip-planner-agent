from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from src.agent.planner_policy import PlanningSlots

SESSION_TTL_SECONDS = 3600  # 1 hour


@dataclass
class SessionState:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    messages: list[dict[str, Any]] = field(default_factory=list)
    route_fetched: bool = False
    accommodation_fetched: bool = False
    weather_fetched: bool = False
    elevation_fetched: bool = False
    tools_used_this_turn: list[str] = field(default_factory=list)
    tool_results_data: dict[str, Any] = field(default_factory=dict)
    planning_slots: PlanningSlots = field(default_factory=PlanningSlots)
    last_active: float = field(default_factory=time.time)


class SessionStore:
    """In-memory session storage keyed by session ID."""

    def __init__(self, ttl: float = SESSION_TTL_SECONDS) -> None:
        self._sessions: dict[str, SessionState] = {}
        self._ttl = ttl

    def get_or_create(self, session_id: str | None = None) -> tuple[SessionState, bool]:
        """Return an existing session or create a new one.

        Returns a tuple of (session, is_new) where is_new is True when
        a requested session_id was not found (e.g. after server restart)
        and a fresh session had to be created.
        """
        self._cleanup_expired()
        if session_id and session_id in self._sessions:
            session = self._sessions[session_id]
            session.last_active = time.time()
            return session, False

        was_requested = session_id is not None
        state = SessionState()
        self._sessions[state.session_id] = state
        return state, was_requested

    def get(self, session_id: str) -> SessionState | None:
        return self._sessions.get(session_id)

    def _cleanup_expired(self) -> None:
        """Remove sessions that have been idle longer than the TTL."""
        now = time.time()
        expired = [
            sid for sid, s in self._sessions.items()
            if now - s.last_active > self._ttl
        ]
        for sid in expired:
            del self._sessions[sid]
