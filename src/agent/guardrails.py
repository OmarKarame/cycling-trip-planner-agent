from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.agent.session import SessionState

# Tools that require the route to be fetched first.
_NEEDS_ROUTE = {"find_accommodation", "get_elevation_profile"}


class ToolGuardrails:
    """Server-side validation applied before executing a tool call."""

    def validate_tool_call(
        self,
        tool_name: str,
        tool_input: dict,
        session: SessionState,
    ) -> tuple[bool, str | None]:
        """Validate whether a tool call is allowed given current session state.

        Returns:
            (is_valid, error_message). If invalid, error_message is sent back
            to Claude as a tool_result error so it can self-correct.
        """
        if tool_name in _NEEDS_ROUTE and not session.route_fetched:
            return False, (
                f"Cannot use {tool_name} yet. Please fetch the route first "
                "using get_route before looking up accommodations or elevation."
            )

        return True, None
