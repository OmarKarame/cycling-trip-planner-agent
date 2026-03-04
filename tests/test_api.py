from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.app import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def _make_mock_response(text: str):
    """Create a mock Claude API response with a text block."""
    text_block = MagicMock()
    text_block.type = "text"
    text_block.text = text

    response = MagicMock()
    response.stop_reason = "end_turn"
    response.content = [text_block]
    return response


class TestChatEndpoint:
    @patch("src.agent.orchestrator.anthropic.AsyncAnthropic")
    def test_new_session_created(self, mock_anthropic_cls, client):
        mock_client = MagicMock()
        mock_client.messages.create = AsyncMock(
            return_value=_make_mock_response(
                "Hello! I'd love to help you plan a cycling trip."
            )
        )
        mock_anthropic_cls.return_value = mock_client

        response = client.post("/chat", json={"message": "Hi"})

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert len(data["session_id"]) > 0
        assert "Hello" in data["response"]

    @patch("src.agent.orchestrator.anthropic.AsyncAnthropic")
    def test_session_persists(self, mock_anthropic_cls, client):
        mock_client = MagicMock()
        mock_client.messages.create = AsyncMock(
            return_value=_make_mock_response("Response 1")
        )
        mock_anthropic_cls.return_value = mock_client

        # First request — creates session
        resp1 = client.post("/chat", json={"message": "Hi"})
        session_id = resp1.json()["session_id"]

        mock_client.messages.create = AsyncMock(
            return_value=_make_mock_response("Response 2")
        )

        # Second request — reuses session
        resp2 = client.post(
            "/chat", json={"message": "Plan a trip", "session_id": session_id}
        )
        assert resp2.json()["session_id"] == session_id

    @patch("src.agent.orchestrator.anthropic.AsyncAnthropic")
    def test_response_format(self, mock_anthropic_cls, client):
        mock_client = MagicMock()
        mock_client.messages.create = AsyncMock(
            return_value=_make_mock_response("Test response")
        )
        mock_anthropic_cls.return_value = mock_client

        response = client.post("/chat", json={"message": "Hello"})
        data = response.json()

        assert "session_id" in data
        assert "response" in data
        assert "tools_used" in data
        assert isinstance(data["tools_used"], list)

    @patch("src.agent.orchestrator.anthropic.AsyncAnthropic")
    def test_expired_session_warns_user(self, mock_anthropic_cls, client):
        """When a session_id is sent but doesn't exist (e.g. server restart),
        the response should include a warning about lost context."""
        mock_client = MagicMock()
        mock_client.messages.create = AsyncMock(
            return_value=_make_mock_response("What trip would you like?")
        )
        mock_anthropic_cls.return_value = mock_client

        response = client.post(
            "/chat",
            json={"message": "add more details", "session_id": "stale-id-123"},
        )

        data = response.json()
        assert response.status_code == 200
        assert "session has expired" in data["response"] or "lost" in data["response"]
        # A new session_id is issued
        assert data["session_id"] != "stale-id-123"

    def test_missing_message_returns_422(self, client):
        response = client.post("/chat", json={})
        assert response.status_code == 422
