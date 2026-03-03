from dataclasses import dataclass

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


@dataclass
class ToolRegistry:
    route: RouteProvider
    accommodation: AccommodationProvider
    weather: WeatherProvider
    elevation: ElevationProvider


def create_mock_registry() -> ToolRegistry:
    """Create a registry with all mock implementations."""
    return ToolRegistry(
        route=MockRouteProvider(),
        accommodation=MockAccommodationProvider(),
        weather=MockWeatherProvider(),
        elevation=MockElevationProvider(),
    )
