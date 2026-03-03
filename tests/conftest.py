import pytest

from src.agent.session import SessionState, SessionStore
from src.tools import ToolRegistry, create_mock_registry


@pytest.fixture
def mock_registry() -> ToolRegistry:
    return create_mock_registry()


@pytest.fixture
def session_store() -> SessionStore:
    return SessionStore()


@pytest.fixture
def session() -> SessionState:
    return SessionState()
