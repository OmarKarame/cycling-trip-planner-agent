import json
import logging

import anthropic

from src.agent.guardrails import ToolGuardrails
from src.agent.planner_policy import (
    build_planning_constraints,
    inject_slot_defaults_into_tool_input,
    update_slots_from_tool_call,
    update_slots_from_user_message,
)
from src.agent.session import SessionState
from src.agent.system_prompt import SYSTEM_PROMPT
from src.agent.tool_definitions import get_tool_definitions
from src.models import (
    AccommodationInput,
    BudgetInput,
    ElevationInput,
    POIInput,
    RouteInput,
    VisaInput,
    WeatherInput,
)
from src.tools import ToolRegistry

logger = logging.getLogger(__name__)

MAX_TOOL_TURNS = 15


# Maps tool names to (input_model, registry_attr, method_name, session_flag).
# session_flag is the SessionState attribute to set True after execution (or None).
_TOOL_DISPATCH: dict[str, tuple[type, str, str, str | None]] = {
    "get_route":              (RouteInput,         "route",         "get_route",              "route_fetched"),
    "find_accommodation":     (AccommodationInput, "accommodation", "find_accommodation",     "accommodation_fetched"),
    "get_weather":            (WeatherInput,       "weather",       "get_weather",            "weather_fetched"),
    "get_elevation_profile":  (ElevationInput,     "elevation",     "get_elevation_profile",  "elevation_fetched"),
    "get_points_of_interest": (POIInput,           "poi",           "get_points_of_interest", None),
    "check_visa_requirements":(VisaInput,          "visa",          "check_visa_requirements",None),
    "estimate_budget":        (BudgetInput,        "budget",        "estimate_budget",        None),
}

# Tools that may be called multiple times per turn (per-waypoint or per-leg) — accumulate as lists.
_ACCUMULATING_TOOLS = {
    "find_accommodation", "get_weather", "get_points_of_interest",
}


class AgentOrchestrator:
    """Runs the hybrid agent loop: Claude picks tools, server validates and executes.

    The server parses user preferences into structured slots and injects them as
    system prompt constraints. Claude drives the conversation flow based on the
    guidelines in the system prompt — the server does not hard-code dialog states.
    """

    def __init__(
        self,
        tool_registry: ToolRegistry,
        model: str = "claude-sonnet-4-20250514",
    ) -> None:
        self.client = anthropic.AsyncAnthropic()
        self.model = model
        self.tools = tool_registry
        self.guardrails = ToolGuardrails()
        self.tool_definitions = get_tool_definitions(tool_registry)

    @staticmethod
    def _trim_messages(messages: list[dict], max_messages: int = 40) -> list[dict]:
        """Keep conversation history within bounds to avoid exceeding the context window.

        Preserves the first user message (trip context) and the most recent turns.
        """
        if len(messages) <= max_messages:
            return messages
        # Keep first message (initial trip description) + most recent messages
        return messages[:1] + messages[-(max_messages - 1):]

    async def chat(self, user_message: str, session: SessionState) -> str:
        """Process a user message and return the agent's text response."""
        session.messages.append({"role": "user", "content": user_message})

        # Parse user preferences into structured slots for system prompt injection.
        update_slots_from_user_message(session.planning_slots, user_message)

        session.tools_used_this_turn = []
        session.messages = self._trim_messages(session.messages)

        logger.info("Processing message for session %s", session.session_id)

        # Agentic tool loop — keeps running until Claude produces a final text response
        for turn in range(MAX_TOOL_TURNS):
            system_prompt = SYSTEM_PROMPT + build_planning_constraints(session)
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                tools=self.tool_definitions,
                messages=session.messages,
            )

            if response.stop_reason == "tool_use":
                # Claude wants to call one or more tools
                session.messages.append(
                    {"role": "assistant", "content": response.content}
                )

                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        logger.info("Tool call: %s", block.name)
                        result = self._execute_tool(
                            block.name, block.input, block.id, session
                        )
                        tool_results.append(result)

                # Send tool results back so Claude can continue
                session.messages.append({"role": "user", "content": tool_results})

            elif response.stop_reason == "end_turn":
                # Claude is done — extract the text portion of the response
                session.messages.append(
                    {"role": "assistant", "content": response.content}
                )
                return self._extract_text(response.content)

            else:
                # Unexpected stop reason — return whatever text we have
                logger.warning("Unexpected stop reason: %s", response.stop_reason)
                session.messages.append(
                    {"role": "assistant", "content": response.content}
                )
                return self._extract_text(response.content)

        logger.error("Hit max tool turns (%d) for session %s", MAX_TOOL_TURNS, session.session_id)
        return self._extract_text(response.content)

    def _execute_tool(
        self,
        tool_name: str,
        tool_input: dict,
        tool_use_id: str,
        session: SessionState,
    ) -> dict:
        """Validate and execute a single tool call."""
        # Apply guardrails (e.g. route must be fetched before accommodation)
        is_valid, error_msg = self.guardrails.validate_tool_call(
            tool_name, tool_input, session
        )
        if not is_valid:
            return {
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": error_msg,
                "is_error": True,
            }

        # Dispatch to the correct provider
        try:
            effective_input = inject_slot_defaults_into_tool_input(
                tool_name, tool_input, session
            )
            update_slots_from_tool_call(
                session.planning_slots, tool_name, effective_input
            )
            result = self._dispatch_tool(tool_name, effective_input, session)
            session.tools_used_this_turn.append(tool_name)
            self._store_tool_result(tool_name, result, session)

            # Fast path: auto-chain weather + elevation + accommodation after route
            if tool_name == "get_route":
                chained = self._auto_chain_after_route(
                    result, effective_input, session
                )
                if chained is not None:
                    return {
                        "type": "tool_result",
                        "tool_use_id": tool_use_id,
                        "content": chained,
                    }

            return {
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": result.model_dump_json(),
            }
        except Exception as e:
            logger.exception("Tool execution failed: %s", tool_name)
            return {
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": f"Tool error: {e}",
                "is_error": True,
            }

    def _dispatch_tool(
        self, tool_name: str, tool_input: dict, session: SessionState
    ):
        """Route a tool call to the correct provider and update session flags."""
        if tool_name not in _TOOL_DISPATCH:
            raise ValueError(f"Unknown tool: {tool_name}")

        input_model, registry_attr, method_name, session_flag = _TOOL_DISPATCH[tool_name]
        parsed = input_model(**tool_input)
        provider = getattr(self.tools, registry_attr)
        result = getattr(provider, method_name)(parsed)

        if session_flag:
            setattr(session, session_flag, True)

        return result

    def _auto_chain_after_route(
        self, route_result, route_input: dict, session: SessionState
    ) -> str | None:
        """Auto-execute weather + elevation + accommodation after get_route.

        Returns enriched JSON content for Claude, or None to fall back to the
        normal tool loop (e.g. when month is unknown).
        """
        slots = session.planning_slots
        if slots.month is None:
            return None

        combined: dict = {
            "_auto_chained": True,
            "route": route_result.model_dump(),
        }

        # Weather (with daily forecasts)
        try:
            weather_input = WeatherInput(
                location=route_input["start"],
                month=slots.month,
                days=route_result.estimated_days,
            )
            weather_result = self.tools.weather.get_weather(weather_input)
            session.weather_fetched = True
            self._store_tool_result("get_weather", weather_result, session)
            session.tools_used_this_turn.append("get_weather")
            combined["weather"] = weather_result.model_dump()
        except Exception as e:
            logger.warning("Auto-chain weather failed: %s", e)
            combined["weather_error"] = str(e)

        # Elevation profile
        try:
            elevation_input = ElevationInput(
                start=route_input["start"],
                end=route_input["end"],
            )
            elevation_result = self.tools.elevation.get_elevation_profile(
                elevation_input
            )
            session.elevation_fetched = True
            self._store_tool_result(
                "get_elevation_profile", elevation_result, session
            )
            session.tools_used_this_turn.append("get_elevation_profile")
            combined["elevation"] = elevation_result.model_dump()
        except Exception as e:
            logger.warning("Auto-chain elevation failed: %s", e)
            combined["elevation_error"] = str(e)

        # Accommodation for every waypoint
        try:
            acc_results = []
            acc_type = slots.accommodation_type
            for wp in route_result.waypoints:
                acc_input = AccommodationInput(
                    location=wp.name,
                    accommodation_type=acc_type,
                )
                acc_result = self.tools.accommodation.find_accommodation(
                    acc_input
                )
                self._store_tool_result(
                    "find_accommodation", acc_result, session
                )
                session.tools_used_this_turn.append("find_accommodation")
                acc_results.append(acc_result.model_dump())
            session.accommodation_fetched = True
            combined["accommodation"] = acc_results
        except Exception as e:
            logger.warning("Auto-chain accommodation failed: %s", e)
            combined["accommodation_error"] = str(e)

        return json.dumps(combined)

    @staticmethod
    def _store_tool_result(tool_name: str, result, session: SessionState) -> None:
        """Store structured tool output on the session for the UI to consume."""
        data = result.model_dump()
        if tool_name in _ACCUMULATING_TOOLS:
            existing = session.tool_results_data.get(tool_name, [])
            existing.append(data)
            session.tool_results_data[tool_name] = existing
        else:
            session.tool_results_data[tool_name] = data

    @staticmethod
    def _extract_text(content) -> str:
        """Pull out all text blocks from a Claude response."""
        parts = []
        for block in content:
            if hasattr(block, "text"):
                parts.append(block.text)
        return "\n".join(parts) if parts else ""
