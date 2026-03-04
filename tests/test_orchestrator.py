"""Tests for the orchestrator's hybrid agent loop.

These tests verify that:
- The tool loop executes tools and returns Claude's final response
- Guardrails block out-of-order calls and Claude self-corrects
- Session state accumulates correctly across tool calls
- The max-turns safety net prevents infinite loops
- Tool errors are handled gracefully
- Slot parsing injects constraints into the system prompt
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.agent.orchestrator import AgentOrchestrator, MAX_TOOL_TURNS
from src.agent.session import SessionState
from src.models import AccommodationType
from src.tools import create_mock_registry


# ── Helpers ──────────────────────────────────────────────────────────


def _tool_use_block(name: str, input: dict, tool_use_id: str | None = None):
    """Create a mock tool_use content block."""
    block = MagicMock(spec=["type", "name", "input", "id"])
    block.type = "tool_use"
    block.name = name
    block.input = input
    block.id = tool_use_id or f"call_{name}"
    return block


def _text_block(text: str):
    """Create a mock text content block."""
    block = MagicMock()
    block.type = "text"
    block.text = text
    return block


def _tool_use_response(*blocks):
    """Claude response that requests tool calls (loop continues)."""
    resp = MagicMock()
    resp.stop_reason = "tool_use"
    resp.content = list(blocks)
    return resp


def _final_response(text: str):
    """Claude response that ends the turn (loop stops)."""
    resp = MagicMock()
    resp.stop_reason = "end_turn"
    resp.content = [_text_block(text)]
    return resp


# ── Fixtures ─────────────────────────────────────────────────────────


@pytest.fixture
def registry():
    return create_mock_registry()


@pytest.fixture
def session():
    return SessionState()


@pytest.fixture
def orchestrator(registry):
    with patch("src.agent.orchestrator.anthropic.AsyncAnthropic"):
        return AgentOrchestrator(tool_registry=registry)


# ── Multi-step planning flow ────────────────────────────────────────


class TestMultiStepPlanning:
    """Verify the agent executes a full planning flow across multiple loop iterations."""

    @pytest.mark.asyncio
    async def test_full_planning_flow_with_auto_chain(self, orchestrator, session):
        """When month is known, get_route auto-chains weather + elevation +
        accommodation server-side, so Claude only needs 2 API calls."""
        orchestrator.client.messages.create = AsyncMock(
            side_effect=[
                _tool_use_response(
                    _tool_use_block("get_route", {
                        "start": "Amsterdam", "end": "Copenhagen",
                    })
                ),
                _final_response("Here is your 8-day cycling trip plan..."),
            ]
        )

        result = await orchestrator.chat(
            "Plan a trip from Amsterdam to Copenhagen in July at 90 km/day, "
            "€70/day, hostels, moderate terrain",
            session,
        )

        assert "cycling trip plan" in result
        # Only 2 API calls: get_route (with auto-chain) + final response
        assert orchestrator.client.messages.create.call_count == 2
        # Auto-chain executed all tools server-side
        assert "get_route" in session.tools_used_this_turn
        assert "get_weather" in session.tools_used_this_turn
        assert "get_elevation_profile" in session.tools_used_this_turn
        assert "find_accommodation" in session.tools_used_this_turn
        # All session flags set
        assert session.route_fetched is True
        assert session.weather_fetched is True
        assert session.elevation_fetched is True
        assert session.accommodation_fetched is True
        # Data stored for UI
        assert "get_route" in session.tool_results_data
        assert "get_weather" in session.tool_results_data
        assert "get_elevation_profile" in session.tool_results_data
        assert "find_accommodation" in session.tool_results_data
        # Accommodation for every waypoint
        acc_data = session.tool_results_data["find_accommodation"]
        assert len(acc_data) >= 8

    @pytest.mark.asyncio
    async def test_session_flags_set_after_each_tool(self, orchestrator, session):
        """Session state flags update as each tool executes."""
        orchestrator.client.messages.create = AsyncMock(
            side_effect=[
                _tool_use_response(
                    _tool_use_block("get_route", {"start": "A", "end": "B"})
                ),
                _tool_use_response(
                    _tool_use_block("get_weather", {"location": "A", "month": 6})
                ),
                _final_response("Done"),
            ]
        )

        await orchestrator.chat("Plan from A to B", session)

        assert session.route_fetched is True
        assert session.weather_fetched is True

    @pytest.mark.asyncio
    async def test_tool_results_stored_on_session(self, orchestrator, session):
        """Structured tool output is accumulated on the session for the UI."""
        orchestrator.client.messages.create = AsyncMock(
            side_effect=[
                _tool_use_response(
                    _tool_use_block("get_route", {
                        "start": "Amsterdam", "end": "Copenhagen",
                    })
                ),
                _tool_use_response(
                    _tool_use_block("get_weather", {"location": "Amsterdam", "month": 7})
                ),
                _final_response("Plan ready."),
            ]
        )

        await orchestrator.chat("Plan trip", session)

        assert "get_route" in session.tool_results_data
        assert "get_weather" in session.tool_results_data
        assert session.tool_results_data["get_route"]["start"] == "Amsterdam"
        assert isinstance(session.tool_results_data["get_weather"], list)
        assert len(session.tool_results_data["get_weather"]) == 1

    @pytest.mark.asyncio
    async def test_accumulating_tools_append(self, orchestrator, session):
        """Weather called for multiple waypoints accumulates as a list."""
        orchestrator.client.messages.create = AsyncMock(
            side_effect=[
                _tool_use_response(
                    _tool_use_block("get_route", {"start": "Amsterdam", "end": "Copenhagen"})
                ),
                _tool_use_response(
                    _tool_use_block("get_weather", {"location": "Amsterdam", "month": 7})
                ),
                _tool_use_response(
                    _tool_use_block("get_weather", {"location": "Copenhagen", "month": 7})
                ),
                _final_response("Done"),
            ]
        )

        await orchestrator.chat("Go", session)

        weather_data = session.tool_results_data["get_weather"]
        assert len(weather_data) == 2
        assert weather_data[0]["location"] == "Amsterdam"
        assert weather_data[1]["location"] == "Copenhagen"

    @pytest.mark.asyncio
    async def test_multiple_tools_in_single_turn(self, orchestrator, session):
        """Claude can request multiple tools in a single response."""
        orchestrator.client.messages.create = AsyncMock(
            side_effect=[
                _tool_use_response(
                    _tool_use_block("get_route", {"start": "Amsterdam", "end": "Copenhagen"}),
                ),
                _tool_use_response(
                    _tool_use_block("get_weather", {"location": "Amsterdam", "month": 7}, "call_1"),
                    _tool_use_block("get_elevation_profile", {
                        "start": "Amsterdam", "end": "Copenhagen",
                    }, "call_2"),
                ),
                _final_response("All done."),
            ]
        )

        await orchestrator.chat("Go", session)

        assert "get_weather" in session.tools_used_this_turn
        assert "get_elevation_profile" in session.tools_used_this_turn
        assert session.weather_fetched is True
        assert session.elevation_fetched is True


# ── Auto-chain fast path ───────────────────────────────────────────


class TestAutoChain:
    """Verify auto-chaining of weather + elevation + accommodation after get_route."""

    @pytest.mark.asyncio
    async def test_auto_chain_skipped_when_month_unknown(self, orchestrator, session):
        """Without a month, auto-chain doesn't fire and the normal loop continues."""
        orchestrator.client.messages.create = AsyncMock(
            side_effect=[
                _tool_use_response(
                    _tool_use_block("get_route", {"start": "A", "end": "B"})
                ),
                _tool_use_response(
                    _tool_use_block("get_weather", {"location": "A", "month": 6})
                ),
                _final_response("Done"),
            ]
        )

        await orchestrator.chat("Plan from A to B", session)

        # Route fetched normally, weather fetched via normal loop
        assert session.route_fetched is True
        assert session.weather_fetched is True
        # No auto-chain — elevation and accommodation not auto-fetched
        assert session.elevation_fetched is False
        assert session.accommodation_fetched is False

    @pytest.mark.asyncio
    async def test_auto_chain_accommodation_matches_waypoints(self, orchestrator, session):
        """Auto-chain creates one accommodation entry per route waypoint."""
        orchestrator.client.messages.create = AsyncMock(
            side_effect=[
                _tool_use_response(
                    _tool_use_block("get_route", {
                        "start": "Amsterdam", "end": "Copenhagen",
                    })
                ),
                _final_response("Here's your plan."),
            ]
        )

        await orchestrator.chat(
            "Plan Amsterdam to Copenhagen in July", session
        )

        route_data = session.tool_results_data["get_route"]
        acc_data = session.tool_results_data["find_accommodation"]
        assert len(acc_data) == len(route_data["waypoints"])

    @pytest.mark.asyncio
    async def test_auto_chain_uses_slot_accommodation_type(self, orchestrator, session):
        """Auto-chain passes the user's accommodation preference to find_accommodation."""
        session.planning_slots.accommodation_type = AccommodationType.CAMPING
        session.planning_slots.month = 8

        orchestrator.client.messages.create = AsyncMock(
            side_effect=[
                _tool_use_response(
                    _tool_use_block("get_route", {
                        "start": "Amsterdam", "end": "Copenhagen",
                    })
                ),
                _final_response("Plan ready."),
            ]
        )

        await orchestrator.chat("Go", session)

        # All accommodation results should be filtered to camping
        acc_data = session.tool_results_data["find_accommodation"]
        for entry in acc_data:
            for acc in entry["accommodations"]:
                assert acc["type"] == "camping"

    @pytest.mark.asyncio
    async def test_auto_chain_content_has_flag(self, orchestrator, session):
        """The enriched tool result contains the _auto_chained flag."""
        orchestrator.client.messages.create = AsyncMock(
            side_effect=[
                _tool_use_response(
                    _tool_use_block("get_route", {
                        "start": "Amsterdam", "end": "Copenhagen",
                    })
                ),
                _final_response("Done."),
            ]
        )

        await orchestrator.chat(
            "Plan Amsterdam to Copenhagen in July", session
        )

        # Check the tool result message sent back to Claude
        tool_result_msg = session.messages[2]  # user → assistant(tool_use) → user(tool_result)
        import json
        content = json.loads(tool_result_msg["content"][0]["content"])
        assert content["_auto_chained"] is True
        assert "route" in content
        assert "weather" in content
        assert "elevation" in content
        assert "accommodation" in content


class TestSlotInjection:
    """Verify that parsed slots are injected into the system prompt."""

    @pytest.mark.asyncio
    async def test_structured_constraints_include_mixed_accommodation(self, orchestrator, session):
        orchestrator.client.messages.create = AsyncMock(
            return_value=_final_response("Great, I will plan this now."),
        )

        await orchestrator.chat(
            "I want to cycle from Amsterdam to Copenhagen in June. "
            "I can do around 100km a day, budget €75/day, "
            "prefer camping but hostel every 4th night, moderate terrain.",
            session,
        )

        system_prompt = orchestrator.client.messages.create.await_args.kwargs["system"]
        assert "Structured Planning Constraints" in system_prompt
        assert "Travel timing: june" in system_prompt
        assert "hostel every 4th night" in system_prompt

    @pytest.mark.asyncio
    async def test_slots_parsed_and_injected_without_blocking(self, orchestrator, session):
        """Even without all preferences, the message goes to Claude (no hard-coded blocking)."""
        orchestrator.client.messages.create = AsyncMock(
            return_value=_final_response("What kind of accommodation do you prefer?"),
        )

        result = await orchestrator.chat(
            "Plan a trip from Amsterdam to Copenhagen in July",
            session,
        )

        # Claude was called (no server-side blocking) and responded naturally
        assert orchestrator.client.messages.create.call_count == 1
        assert "accommodation" in result


# ── Guardrail self-correction ───────────────────────────────────────


class TestGuardrailSelfCorrection:
    """Verify that guardrails block out-of-order tool calls and the loop
    gives Claude a chance to self-correct."""

    @pytest.mark.asyncio
    async def test_accommodation_blocked_then_self_corrects(self, orchestrator, session):
        """Claude tries accommodation first (blocked), then calls route + weather,
        then retries accommodation (allowed)."""
        orchestrator.client.messages.create = AsyncMock(
            side_effect=[
                _tool_use_response(
                    _tool_use_block("find_accommodation", {"location": "Berlin"})
                ),
                _tool_use_response(
                    _tool_use_block("get_route", {"start": "Berlin", "end": "Prague"})
                ),
                _tool_use_response(
                    _tool_use_block("get_weather", {"location": "Berlin", "month": 8})
                ),
                _tool_use_response(
                    _tool_use_block("find_accommodation", {"location": "Berlin"})
                ),
                _final_response("Here's your trip plan."),
            ]
        )

        result = await orchestrator.chat("Plan Berlin to Prague", session)

        assert "trip plan" in result
        assert session.tools_used_this_turn == [
            "get_route", "get_weather", "find_accommodation",
        ]

    @pytest.mark.asyncio
    async def test_blocked_tool_returns_error_to_claude(self, orchestrator, session):
        """When a guardrail blocks a tool, the error is sent back as a tool_result
        with is_error=True so Claude sees it in context."""
        orchestrator.client.messages.create = AsyncMock(
            side_effect=[
                _tool_use_response(
                    _tool_use_block("find_accommodation", {"location": "Berlin"}, "call_1")
                ),
                _final_response("I need to get the route first."),
            ]
        )

        await orchestrator.chat("Find hotels", session)

        tool_result_msg = session.messages[2]  # [user_msg, assistant_tool_use, user_tool_result]
        assert tool_result_msg["role"] == "user"
        tool_result = tool_result_msg["content"][0]
        assert tool_result["is_error"] is True
        assert "get_route" in tool_result["content"]

    @pytest.mark.asyncio
    async def test_elevation_blocked_without_route(self, orchestrator, session):
        """Elevation is blocked if route hasn't been fetched yet."""
        orchestrator.client.messages.create = AsyncMock(
            side_effect=[
                _tool_use_response(
                    _tool_use_block("get_elevation_profile", {"start": "A", "end": "B"})
                ),
                _final_response("Let me get the route first."),
            ]
        )

        await orchestrator.chat("Check elevation", session)

        assert "get_elevation_profile" not in session.tools_used_this_turn
        assert session.elevation_fetched is False

    @pytest.mark.asyncio
    async def test_accommodation_needs_both_route_and_weather(self, orchestrator, session):
        """Accommodation is blocked even with route if weather hasn't been checked."""
        orchestrator.client.messages.create = AsyncMock(
            side_effect=[
                _tool_use_response(
                    _tool_use_block("get_route", {"start": "A", "end": "B"})
                ),
                _tool_use_response(
                    _tool_use_block("find_accommodation", {"location": "A"})
                ),
                _tool_use_response(
                    _tool_use_block("get_weather", {"location": "A", "month": 6})
                ),
                _tool_use_response(
                    _tool_use_block("find_accommodation", {"location": "A"})
                ),
                _final_response("Done."),
            ]
        )

        await orchestrator.chat("Plan trip", session)

        assert session.route_fetched is True
        assert session.weather_fetched is True
        assert session.accommodation_fetched is True
        assert session.tools_used_this_turn == [
            "get_route", "get_weather", "find_accommodation",
        ]


# ── Max turns safety ────────────────────────────────────────────────


class TestMaxTurnsSafety:
    """Verify the loop terminates if Claude keeps requesting tools."""

    @pytest.mark.asyncio
    async def test_max_turns_stops_infinite_loop(self, orchestrator, session):
        """If Claude calls tools MAX_TOOL_TURNS times without stopping,
        the loop terminates and returns whatever text is available."""
        orchestrator.client.messages.create = AsyncMock(
            side_effect=[
                _tool_use_response(
                    _tool_use_block("get_route", {"start": "A", "end": "B"})
                )
            ] * MAX_TOOL_TURNS
        )

        result = await orchestrator.chat("Plan a trip", session)

        assert orchestrator.client.messages.create.call_count == MAX_TOOL_TURNS
        assert isinstance(result, str)


# ── Tool error handling ─────────────────────────────────────────────


class TestToolErrorHandling:
    """Verify tool exceptions are caught and sent back to Claude as errors."""

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error(self, orchestrator, session):
        """An unknown tool name produces a tool_result error, not a crash."""
        orchestrator.client.messages.create = AsyncMock(
            side_effect=[
                _tool_use_response(
                    _tool_use_block("nonexistent_tool", {})
                ),
                _final_response("Sorry, that tool doesn't exist."),
            ]
        )

        result = await orchestrator.chat("Do something", session)

        assert isinstance(result, str)
        assert "nonexistent_tool" not in session.tools_used_this_turn

    @pytest.mark.asyncio
    async def test_tool_with_invalid_input_returns_error(self, orchestrator, session):
        """Invalid tool input (e.g. missing required field) produces an error,
        not a crash."""
        orchestrator.client.messages.create = AsyncMock(
            side_effect=[
                _tool_use_response(
                    _tool_use_block("get_weather", {"location": "A", "month": 99})
                ),
                _final_response("Let me fix that."),
            ]
        )

        result = await orchestrator.chat("Check weather", session)

        assert isinstance(result, str)


# ── Message history ─────────────────────────────────────────────────


class TestMessageHistory:
    """Verify the orchestrator builds the correct message history."""

    @pytest.mark.asyncio
    async def test_messages_alternate_correctly(self, orchestrator, session):
        """After a multi-tool flow, messages alternate assistant/user correctly."""
        orchestrator.client.messages.create = AsyncMock(
            side_effect=[
                _tool_use_response(
                    _tool_use_block("get_route", {"start": "A", "end": "B"})
                ),
                _final_response("Done."),
            ]
        )

        await orchestrator.chat("Plan trip", session)

        roles = [m["role"] for m in session.messages]
        # user → assistant(tool_use) → user(tool_result) → assistant(end_turn)
        assert roles == ["user", "assistant", "user", "assistant"]

    @pytest.mark.asyncio
    async def test_trim_messages_preserves_first_and_recent(self, orchestrator, session):
        """_trim_messages keeps the first message and most recent messages."""
        messages = [{"role": "user", "content": f"msg_{i}"} for i in range(50)]
        trimmed = orchestrator._trim_messages(messages, max_messages=10)

        assert len(trimmed) == 10
        assert trimmed[0]["content"] == "msg_0"
        assert trimmed[-1]["content"] == "msg_49"

    @pytest.mark.asyncio
    async def test_trim_messages_noop_when_under_limit(self, orchestrator, session):
        """No trimming when message count is within bounds."""
        messages = [{"role": "user", "content": f"msg_{i}"} for i in range(5)]
        trimmed = orchestrator._trim_messages(messages, max_messages=10)

        assert len(trimmed) == 5

    @pytest.mark.asyncio
    async def test_second_turn_preserves_context(self, orchestrator, session):
        """A second user message appends to the existing history, preserving context."""
        orchestrator.client.messages.create = AsyncMock(
            side_effect=[
                _final_response("What route?"),
                _final_response("Got it, Amsterdam to Copenhagen."),
            ]
        )

        await orchestrator.chat("Hi", session)
        await orchestrator.chat("Amsterdam to Copenhagen", session)

        user_messages = [
            m["content"] for m in session.messages if m["role"] == "user"
        ]
        assert "Hi" in user_messages
        assert "Amsterdam to Copenhagen" in user_messages
