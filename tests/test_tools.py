from src.models import (
    AccommodationInput,
    AccommodationType,
    DifficultyRating,
    ElevationInput,
    RouteInput,
    WeatherInput,
)
from src.tools.mock_accommodation import MockAccommodationProvider
from src.tools.mock_elevation import MockElevationProvider
from src.tools.mock_route import MockRouteProvider
from src.tools.mock_weather import MockWeatherProvider
from src.tools.protocol import (
    AccommodationProvider,
    ElevationProvider,
    RouteProvider,
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
