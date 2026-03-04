from src.agent.guardrails import ToolGuardrails
from src.agent.session import SessionState


class TestToolGuardrails:
    def setup_method(self):
        self.guardrails = ToolGuardrails()

    def test_get_route_always_allowed(self):
        session = SessionState()
        valid, error = self.guardrails.validate_tool_call("get_route", {}, session)
        assert valid is True
        assert error is None

    def test_get_weather_blocked_without_route(self):
        session = SessionState()
        valid, error = self.guardrails.validate_tool_call("get_weather", {}, session)
        assert valid is False
        assert "get_route" in error

    def test_get_weather_allowed_with_route(self):
        session = SessionState(route_fetched=True)
        valid, error = self.guardrails.validate_tool_call("get_weather", {}, session)
        assert valid is True
        assert error is None

    def test_accommodation_blocked_without_route(self):
        session = SessionState()
        valid, error = self.guardrails.validate_tool_call(
            "find_accommodation", {}, session
        )
        assert valid is False
        assert "get_route" in error

    def test_accommodation_blocked_without_weather(self):
        session = SessionState(route_fetched=True)
        valid, error = self.guardrails.validate_tool_call(
            "find_accommodation", {}, session
        )
        assert valid is False
        assert "get_weather" in error

    def test_accommodation_allowed_with_route_and_weather(self):
        session = SessionState(route_fetched=True, weather_fetched=True)
        valid, error = self.guardrails.validate_tool_call(
            "find_accommodation", {}, session
        )
        assert valid is True
        assert error is None

    def test_elevation_blocked_without_route(self):
        session = SessionState()
        valid, error = self.guardrails.validate_tool_call(
            "get_elevation_profile", {}, session
        )
        assert valid is False

    def test_elevation_allowed_with_route(self):
        session = SessionState(route_fetched=True)
        valid, error = self.guardrails.validate_tool_call(
            "get_elevation_profile", {}, session
        )
        assert valid is True

    def test_poi_blocked_without_route(self):
        session = SessionState()
        valid, error = self.guardrails.validate_tool_call(
            "get_points_of_interest", {}, session
        )
        assert valid is False
        assert "get_route" in error

    def test_poi_allowed_with_route(self):
        session = SessionState(route_fetched=True)
        valid, error = self.guardrails.validate_tool_call(
            "get_points_of_interest", {}, session
        )
        assert valid is True

    def test_visa_always_allowed(self):
        session = SessionState()
        valid, error = self.guardrails.validate_tool_call(
            "check_visa_requirements", {}, session
        )
        assert valid is True

    def test_budget_blocked_without_route(self):
        session = SessionState()
        valid, error = self.guardrails.validate_tool_call(
            "estimate_budget", {}, session
        )
        assert valid is False

    def test_budget_allowed_with_route(self):
        session = SessionState(route_fetched=True)
        valid, error = self.guardrails.validate_tool_call(
            "estimate_budget", {}, session
        )
        assert valid is True
