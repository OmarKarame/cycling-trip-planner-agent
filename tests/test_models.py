import pytest
from pydantic import ValidationError

from src.models import (
    Accommodation,
    AccommodationInput,
    AccommodationType,
    ChatRequest,
    ChatResponse,
    DifficultyRating,
    ElevationInput,
    RouteInput,
    Waypoint,
    WeatherInput,
)


class TestRouteModels:
    def test_route_input_defaults(self):
        ri = RouteInput(start="Paris", end="Amsterdam")
        assert ri.daily_distance_km == 100.0

    def test_route_input_custom_distance(self):
        ri = RouteInput(start="A", end="B", daily_distance_km=80.0)
        assert ri.daily_distance_km == 80.0

    def test_waypoint_valid(self):
        wp = Waypoint(name="Test", latitude=52.0, longitude=4.0, day=1)
        assert wp.name == "Test"


class TestAccommodationModels:
    def test_accommodation_rating_bounds(self):
        acc = Accommodation(
            name="Test", type=AccommodationType.HOSTEL,
            price_per_night=30.0, rating=4.5, location="Berlin",
        )
        assert acc.rating == 4.5

    def test_accommodation_rating_too_high(self):
        with pytest.raises(ValidationError):
            Accommodation(
                name="Test", type=AccommodationType.HOSTEL,
                price_per_night=30.0, rating=6.0, location="Berlin",
            )

    def test_accommodation_rating_negative(self):
        with pytest.raises(ValidationError):
            Accommodation(
                name="Test", type=AccommodationType.HOSTEL,
                price_per_night=30.0, rating=-1.0, location="Berlin",
            )

    def test_accommodation_input_defaults(self):
        ai = AccommodationInput(location="Berlin")
        assert ai.accommodation_type is None
        assert ai.max_price is None


class TestWeatherModels:
    def test_valid_month(self):
        wi = WeatherInput(location="Paris", month=6)
        assert wi.month == 6

    def test_month_too_low(self):
        with pytest.raises(ValidationError):
            WeatherInput(location="Paris", month=0)

    def test_month_too_high(self):
        with pytest.raises(ValidationError):
            WeatherInput(location="Paris", month=13)

    def test_days_optional(self):
        wi = WeatherInput(location="Paris", month=6)
        assert wi.days is None

    def test_days_provided(self):
        wi = WeatherInput(location="Paris", month=6, days=8)
        assert wi.days == 8

    def test_days_must_be_positive(self):
        with pytest.raises(ValidationError):
            WeatherInput(location="Paris", month=6, days=0)


class TestElevationModels:
    def test_valid_input(self):
        ei = ElevationInput(start="Berlin", end="Prague")
        assert ei.start == "Berlin"

    def test_difficulty_enum_values(self):
        assert DifficultyRating.EASY.value == "easy"
        assert DifficultyRating.EXTREME.value == "extreme"


class TestPOIModels:
    def test_poi_input_defaults(self):
        from src.models import POIInput
        pi = POIInput(location="Amsterdam")
        assert pi.radius_km == 20.0

    def test_poi_category_values(self):
        from src.models import POICategory
        assert POICategory.HISTORICAL.value == "historical"
        assert POICategory.VIEWPOINT.value == "viewpoint"


class TestVisaModels:
    def test_visa_input(self):
        from src.models import VisaInput
        vi = VisaInput(nationality="Dutch", countries=["Germany", "Denmark"])
        assert len(vi.countries) == 2

    def test_visa_requirement(self):
        from src.models import VisaRequirement
        vr = VisaRequirement(
            country="Germany", visa_required=False,
            notes="No visa required.",
        )
        assert vr.visa_type is None


class TestBudgetModels:
    def test_budget_input_defaults(self):
        from src.models import BudgetInput
        bi = BudgetInput(start="Amsterdam", end="Copenhagen", days=10)
        assert bi.accommodation_type == AccommodationType.HOSTEL
        assert bi.budget_level == "moderate"

    def test_budget_breakdown(self):
        from src.models import BudgetBreakdown
        bb = BudgetBreakdown(
            accommodation=40, food=35, transport=8, activities=10, total=93,
        )
        assert bb.total == 93


class TestAPIModels:
    def test_chat_request_without_session(self):
        req = ChatRequest(message="Hello")
        assert req.session_id is None

    def test_chat_request_with_session(self):
        req = ChatRequest(message="Hello", session_id="abc-123")
        assert req.session_id == "abc-123"

    def test_chat_response_defaults(self):
        resp = ChatResponse(session_id="x", response="Hi there")
        assert resp.tools_used == []
