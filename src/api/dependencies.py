from functools import lru_cache

from src.agent.orchestrator import AgentOrchestrator
from src.agent.session import SessionStore
from src.tools import create_mock_registry


@lru_cache()
def get_session_store() -> SessionStore:
    return SessionStore()


@lru_cache()
def get_orchestrator() -> AgentOrchestrator:
    registry = create_mock_registry()
    return AgentOrchestrator(tool_registry=registry)
