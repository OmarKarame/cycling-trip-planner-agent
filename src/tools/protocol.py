from typing import Protocol, runtime_checkable

from src.models import (
    AccommodationInput,
    AccommodationOutput,
    BudgetInput,
    BudgetOutput,
    ElevationInput,
    ElevationOutput,
    POIInput,
    POIOutput,
    RouteInput,
    RouteOutput,
    VisaInput,
    VisaOutput,
    WeatherInput,
    WeatherOutput,
)


@runtime_checkable
class RouteProvider(Protocol):
    def get_route(self, input: RouteInput) -> RouteOutput: ...


@runtime_checkable
class AccommodationProvider(Protocol):
    def find_accommodation(self, input: AccommodationInput) -> AccommodationOutput: ...


@runtime_checkable
class WeatherProvider(Protocol):
    def get_weather(self, input: WeatherInput) -> WeatherOutput: ...


@runtime_checkable
class ElevationProvider(Protocol):
    def get_elevation_profile(self, input: ElevationInput) -> ElevationOutput: ...


@runtime_checkable
class POIProvider(Protocol):
    def get_points_of_interest(self, input: POIInput) -> POIOutput: ...


@runtime_checkable
class VisaProvider(Protocol):
    def check_visa_requirements(self, input: VisaInput) -> VisaOutput: ...


@runtime_checkable
class BudgetProvider(Protocol):
    def estimate_budget(self, input: BudgetInput) -> BudgetOutput: ...
