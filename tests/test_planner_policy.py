from src.agent.planner_policy import (
    PlanningSlots,
    build_planning_constraints,
    inject_slot_defaults_into_tool_input,
    update_slots_from_user_message,
)
from src.agent.session import SessionState
from src.models import AccommodationType, DifficultyRating


class TestSlotExtraction:
    def test_extract_required_slots_from_user_message(self):
        slots = PlanningSlots()

        captured = update_slots_from_user_message(
            slots,
            "Plan a trip from Amsterdam to Copenhagen in July",
        )

        assert captured == {"start", "end", "month"}
        assert slots.start == "Amsterdam"
        assert slots.end == "Copenhagen"
        assert slots.month == 7

    def test_extracts_preference_fields_from_message(self):
        slots = PlanningSlots()
        captured = update_slots_from_user_message(
            slots,
            "I can do 85 km/day, budget €70/day, hostels, moderate terrain.",
        )

        assert "daily_distance_km" in captured
        assert "budget_per_day_eur" in captured
        assert "accommodation_type" in captured
        assert "difficulty_preference" in captured
        assert slots.daily_distance_km == 85.0
        assert slots.budget_per_day_eur == 70.0
        assert slots.accommodation_type.value == "hostel"
        assert slots.difficulty_preference.value == "moderate"

    def test_extracts_distance_from_natural_phrase(self):
        slots = PlanningSlots()
        captured = update_slots_from_user_message(
            slots,
            "I can do around 100km a day and prefer camping.",
        )

        assert "daily_distance_km" in captured
        assert slots.daily_distance_km == 100.0

    def test_extracts_mixed_accommodation_pattern(self):
        slots = PlanningSlots()
        captured = update_slots_from_user_message(
            slots,
            "I prefer camping but want a hostel every 4th night.",
        )

        assert "accommodation_type" in captured
        assert slots.accommodation_type.value == "camping"
        assert slots.accommodation_secondary_type.value == "hostel"
        assert slots.accommodation_secondary_every_n_nights == 4

    def test_extracts_travel_month_phrase(self):
        slots = PlanningSlots()
        captured = update_slots_from_user_message(
            slots,
            "Traveling in June.",
        )

        assert "month" in captured
        assert slots.month == 6
        assert slots.travel_timing_note == "june"
        assert slots.travel_timing_is_approximate is False

    def test_extracts_season_as_approximate_travel_timing(self):
        slots = PlanningSlots()
        captured = update_slots_from_user_message(
            slots,
            "We're aiming for summer.",
        )

        assert "month" in captured
        assert slots.month == 7
        assert slots.travel_timing_note == "summer"
        assert slots.travel_timing_is_approximate is True

    def test_tool_input_is_enriched_from_slots(self):
        session = SessionState()
        session.planning_slots.daily_distance_km = 95.0
        session.planning_slots.month = 6

        route_input = inject_slot_defaults_into_tool_input("get_route", {"start": "A", "end": "B"}, session)
        weather_input = inject_slot_defaults_into_tool_input("get_weather", {"location": "A"}, session)

        assert route_input["daily_distance_km"] == 95.0
        assert weather_input["month"] == 6

    def test_build_planning_constraints_includes_mixed_accommodation(self):
        session = SessionState()
        session.planning_slots.start = "Amsterdam"
        session.planning_slots.end = "Copenhagen"
        session.planning_slots.travel_timing_note = "june"
        session.planning_slots.month = 6
        session.planning_slots.daily_distance_km = 100.0
        session.planning_slots.budget_per_day_eur = 70.0
        session.planning_slots.accommodation_type = AccommodationType.CAMPING
        session.planning_slots.accommodation_secondary_type = AccommodationType.HOSTEL
        session.planning_slots.accommodation_secondary_every_n_nights = 4
        session.planning_slots.difficulty_preference = DifficultyRating.MODERATE

        constraints = build_planning_constraints(session)
        assert "Structured Planning Constraints" in constraints
        assert "hostel every 4th night" in constraints

