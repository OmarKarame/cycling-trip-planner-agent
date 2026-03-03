from typing import Protocol, runtime_checkable

from src.models import (
    AccommodationInput,
    AccommodationOutput,
    ElevationInput,
    ElevationOutput,
    RouteInput,
    RouteOutput,
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
