from dataclasses import dataclass, field
from typing import Optional

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


@dataclass
class ToolRegistry:
    route: RouteProvider
    accommodation: AccommodationProvider
    weather: WeatherProvider
    elevation: ElevationProvider
    poi: Optional[POIProvider] = field(default=None)
    visa: Optional[VisaProvider] = field(default=None)
    budget: Optional[BudgetProvider] = field(default=None)


def create_mock_registry() -> ToolRegistry:
    """Create a registry with all mock implementations."""
    return ToolRegistry(
        route=MockRouteProvider(),
        accommodation=MockAccommodationProvider(),
        weather=MockWeatherProvider(),
        elevation=MockElevationProvider(),
        poi=MockPOIProvider(),
        visa=MockVisaProvider(),
        budget=MockBudgetProvider(),
    )
