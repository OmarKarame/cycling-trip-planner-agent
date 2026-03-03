import anthropic

from src.agent.guardrails import ToolGuardrails
from src.agent.session import SessionState
from src.agent.system_prompt import SYSTEM_PROMPT
from src.agent.tool_definitions import get_tool_definitions
from src.models import (
    AccommodationInput,
    ElevationInput,
    RouteInput,
    WeatherInput,
)
from src.tools import ToolRegistry


class AgentOrchestrator:
    """Runs the hybrid agent loop: Claude picks tools, server validates and executes."""

    def __init__(
        self,
        tool_registry: ToolRegistry,
        model: str = "claude-opus-4-20250514",
    ) -> None:
        self.client = anthropic.Anthropic()
        self.model = model
        self.tools = tool_registry
        self.guardrails = ToolGuardrails()
        self.tool_definitions = get_tool_definitions(tool_registry)

    async def chat(self, user_message: str, session: SessionState) -> str:
        """Process a user message and return the agent's text response."""
        session.messages.append({"role": "user", "content": user_message})
        session.tools_used_this_turn = []

        # Agentic tool loop — keeps running until Claude produces a final text response
        while True:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=4096,
                system=SYSTEM_PROMPT,
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
                session.messages.append(
                    {"role": "assistant", "content": response.content}
                )
                return self._extract_text(response.content)

    def _execute_tool(
        self,
        tool_name: str,
        tool_input: dict,
        tool_use_id: str,
        session: SessionState,
    ) -> dict:
        """Validate and execute a single tool call."""
        # Apply guardrails first
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
            result = self._dispatch_tool(tool_name, tool_input, session)
            session.tools_used_this_turn.append(tool_name)
            return {
                "type": "tool_result",
                "tool_use_id": tool_use_id,
                "content": result.model_dump_json(),
            }
        except Exception as e:
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
        match tool_name:
            case "get_route":
                parsed = RouteInput(**tool_input)
                result = self.tools.route.get_route(parsed)
                session.route_fetched = True
                return result
            case "find_accommodation":
                parsed = AccommodationInput(**tool_input)
                result = self.tools.accommodation.find_accommodation(parsed)
                session.accommodation_fetched = True
                return result
            case "get_weather":
                parsed = WeatherInput(**tool_input)
                result = self.tools.weather.get_weather(parsed)
                session.weather_fetched = True
                return result
            case "get_elevation_profile":
                parsed = ElevationInput(**tool_input)
                result = self.tools.elevation.get_elevation_profile(parsed)
                session.elevation_fetched = True
                return result
            case _:
                raise ValueError(f"Unknown tool: {tool_name}")

    @staticmethod
    def _extract_text(content) -> str:
        """Pull out all text blocks from a Claude response."""
        parts = []
        for block in content:
            if hasattr(block, "text"):
                parts.append(block.text)
        return "\n".join(parts) if parts else ""
