from src.models import (
    AccommodationInput,
    AccommodationType,
    BudgetInput,
    DifficultyRating,
    ElevationInput,
    POIInput,
    RouteInput,
    VisaInput,
    WeatherInput,
)
from src.tools.mock_accommodation import MockAccommodationProvider
from src.tools.mock_budget import MockBudgetProvider
from src.tools.mock_elevation import MockElevationProvider
from src.tools.mock_poi import MockPOIProvider
from src.tools.mock_route import MockRouteProvider
from src.tools.mock_visa import MockVisaProvider
from src.tools.mock_weather import MockWeatherProvider
from src.tools.protocol import (
    AccommodationProvider,
    BudgetProvider,
    ElevationProvider,
    POIProvider,
    RouteProvider,
    VisaProvider,
    WeatherProvider,
)


class TestMockRoute:
    def test_satisfies_protocol(self):
        assert isinstance(MockRouteProvider(), RouteProvider)

    def test_known_route(self):
        provider = MockRouteProvider()
        result = provider.get_route(RouteInput(start="Amsterdam", end="Copenhagen"))
        assert result.total_distance_km == 810.0
        assert result.estimated_days > 0
        assert len(result.waypoints) > 0
        assert result.waypoints[0].name == "Amsterdam"
        assert result.waypoints[-1].name == "Copenhagen"

    def test_known_route_case_insensitive(self):
        provider = MockRouteProvider()
        result = provider.get_route(RouteInput(start="amsterdam", end="copenhagen"))
        assert result.total_distance_km == 810.0

    def test_reverse_route(self):
        provider = MockRouteProvider()
        result = provider.get_route(RouteInput(start="Copenhagen", end="Amsterdam"))
        assert result.total_distance_km == 810.0
        assert result.waypoints[0].name == "Copenhagen"

    def test_unknown_route_fallback(self):
        provider = MockRouteProvider()
        result = provider.get_route(RouteInput(start="London", end="Edinburgh"))
        assert result.total_distance_km > 0
        assert result.estimated_days > 0
        assert result.start == "London"
        assert result.end == "Edinburgh"

    def test_custom_daily_distance(self):
        provider = MockRouteProvider()
        result = provider.get_route(
            RouteInput(start="Amsterdam", end="Copenhagen", daily_distance_km=80.0)
        )
        # More days needed at lower daily distance
        assert result.estimated_days >= 10


class TestMockAccommodation:
    def test_satisfies_protocol(self):
        assert isinstance(MockAccommodationProvider(), AccommodationProvider)

    def test_returns_all_types(self):
        provider = MockAccommodationProvider()
        result = provider.find_accommodation(AccommodationInput(location="Berlin"))
        types_found = {a.type for a in result.accommodations}
        assert AccommodationType.CAMPING in types_found
        assert AccommodationType.HOSTEL in types_found
        assert AccommodationType.HOTEL in types_found

    def test_filter_by_type(self):
        provider = MockAccommodationProvider()
        result = provider.find_accommodation(
            AccommodationInput(location="Berlin", accommodation_type=AccommodationType.CAMPING)
        )
        assert all(a.type == AccommodationType.CAMPING for a in result.accommodations)

    def test_filter_by_max_price(self):
        provider = MockAccommodationProvider()
        result = provider.find_accommodation(
            AccommodationInput(location="Berlin", max_price=30.0)
        )
        assert all(a.price_per_night <= 30.0 for a in result.accommodations)

    def test_location_in_name(self):
        provider = MockAccommodationProvider()
        result = provider.find_accommodation(AccommodationInput(location="Hamburg"))
        assert all("Hamburg" in a.name for a in result.accommodations)


class TestMockWeather:
    def test_satisfies_protocol(self):
        assert isinstance(MockWeatherProvider(), WeatherProvider)

    def test_summer_weather(self):
        provider = MockWeatherProvider()
        result = provider.get_weather(WeatherInput(location="Berlin", month=7))
        assert result.avg_temp_celsius > 15.0
        assert result.rain_chance_percent < 30.0

    def test_winter_weather(self):
        provider = MockWeatherProvider()
        result = provider.get_weather(WeatherInput(location="Berlin", month=1))
        assert result.avg_temp_celsius < 10.0

    def test_location_in_summary(self):
        provider = MockWeatherProvider()
        result = provider.get_weather(WeatherInput(location="Paris", month=6))
        assert "Paris" in result.summary

    def test_no_daily_forecasts_without_days(self):
        provider = MockWeatherProvider()
        result = provider.get_weather(WeatherInput(location="Berlin", month=7))
        assert result.daily_forecasts is None

    def test_daily_forecasts_returned_with_days(self):
        provider = MockWeatherProvider()
        result = provider.get_weather(
            WeatherInput(location="Berlin", month=7, days=8)
        )
        assert result.daily_forecasts is not None
        assert len(result.daily_forecasts) == 8
        assert result.daily_forecasts[0].day == 1
        assert result.daily_forecasts[-1].day == 8

    def test_daily_forecasts_have_variation(self):
        provider = MockWeatherProvider()
        result = provider.get_weather(
            WeatherInput(location="Berlin", month=7, days=5)
        )
        temps = [f.avg_temp_celsius for f in result.daily_forecasts]
        # Not all identical — there should be some variation
        assert len(set(temps)) > 1

    def test_daily_forecasts_rain_chance_bounded(self):
        provider = MockWeatherProvider()
        result = provider.get_weather(
            WeatherInput(location="Berlin", month=7, days=10)
        )
        for f in result.daily_forecasts:
            assert 0.0 <= f.rain_chance_percent <= 100.0
            assert f.wind_speed_kmh >= 0.0


class TestMockElevation:
    def test_satisfies_protocol(self):
        assert isinstance(MockElevationProvider(), ElevationProvider)

    def test_flat_terrain(self):
        provider = MockElevationProvider()
        result = provider.get_elevation_profile(
            ElevationInput(start="Amsterdam", end="Copenhagen")
        )
        assert result.difficulty == DifficultyRating.EASY

    def test_mountainous_terrain(self):
        provider = MockElevationProvider()
        result = provider.get_elevation_profile(
            ElevationInput(start="Geneva", end="Alps Pass")
        )
        assert result.difficulty == DifficultyRating.HARD
        assert result.total_elevation_gain_m > 2000

    def test_output_fields(self):
        provider = MockElevationProvider()
        result = provider.get_elevation_profile(
            ElevationInput(start="A", end="B")
        )
        assert result.total_elevation_gain_m >= 0
        assert result.max_elevation_m >= 0


class TestMockPOI:
    def test_satisfies_protocol(self):
        assert isinstance(MockPOIProvider(), POIProvider)

    def test_returns_pois(self):
        provider = MockPOIProvider()
        result = provider.get_points_of_interest(POIInput(location="Amsterdam"))
        assert len(result.points_of_interest) > 0
        assert result.location == "Amsterdam"

    def test_poi_has_required_fields(self):
        provider = MockPOIProvider()
        result = provider.get_points_of_interest(POIInput(location="Berlin"))
        poi = result.points_of_interest[0]
        assert poi.name
        assert poi.category
        assert poi.description
        assert poi.detour_km >= 0

    def test_known_location_has_realistic_names(self):
        provider = MockPOIProvider()
        result = provider.get_points_of_interest(POIInput(location="London"))
        names = [poi.name for poi in result.points_of_interest]
        # Should NOT just be "London Cathedral", "London Market" etc.
        assert not any(name.startswith("London ") and name.endswith("Cathedral") for name in names)
        # Should have real place names
        assert any("St Paul" in name or "Tower" in name or "Borough" in name for name in names)

    def test_known_location_case_insensitive(self):
        provider = MockPOIProvider()
        result = provider.get_points_of_interest(POIInput(location="london"))
        assert len(result.points_of_interest) > 0

    def test_unknown_location_fallback(self):
        provider = MockPOIProvider()
        result = provider.get_points_of_interest(POIInput(location="Smalltown"))
        assert len(result.points_of_interest) > 0
        # Fallback uses generic but not city-name-prefixed templates
        names = [poi.name for poi in result.points_of_interest]
        assert any("Old Town" in name or "Riverside" in name or "Market" in name for name in names)

    def test_radius_filters_pois(self):
        provider = MockPOIProvider()
        small = provider.get_points_of_interest(POIInput(location="London", radius_km=1.0))
        large = provider.get_points_of_interest(POIInput(location="London", radius_km=50.0))
        assert len(small.points_of_interest) <= len(large.points_of_interest)


class TestMockVisa:
    def test_satisfies_protocol(self):
        assert isinstance(MockVisaProvider(), VisaProvider)

    def test_eu_citizen_in_schengen(self):
        provider = MockVisaProvider()
        result = provider.check_visa_requirements(
            VisaInput(nationality="Dutch", countries=["Germany", "Denmark"])
        )
        assert len(result.requirements) == 2
        assert all(not r.visa_required for r in result.requirements)

    def test_visa_required_country(self):
        provider = MockVisaProvider()
        result = provider.check_visa_requirements(
            VisaInput(nationality="Dutch", countries=["Turkey"])
        )
        assert result.requirements[0].visa_required is True

    def test_nationality_preserved(self):
        provider = MockVisaProvider()
        result = provider.check_visa_requirements(
            VisaInput(nationality="Canadian", countries=["France"])
        )
        assert result.nationality == "Canadian"


class TestMockBudget:
    def test_satisfies_protocol(self):
        assert isinstance(MockBudgetProvider(), BudgetProvider)

    def test_budget_calculation(self):
        provider = MockBudgetProvider()
        result = provider.estimate_budget(
            BudgetInput(start="Amsterdam", end="Copenhagen", days=10)
        )
        assert result.daily_estimate.total > 0
        assert result.total_estimate.total == result.daily_estimate.total * 10
        assert result.currency == "EUR"

    def test_budget_levels_differ(self):
        provider = MockBudgetProvider()
        budget = provider.estimate_budget(
            BudgetInput(start="A", end="B", days=5, budget_level="budget")
        )
        comfort = provider.estimate_budget(
            BudgetInput(start="A", end="B", days=5, budget_level="comfort")
        )
        assert comfort.daily_estimate.total > budget.daily_estimate.total

    def test_tips_included(self):
        provider = MockBudgetProvider()
        result = provider.estimate_budget(
            BudgetInput(start="A", end="B", days=5)
        )
        assert len(result.tips) > 0
