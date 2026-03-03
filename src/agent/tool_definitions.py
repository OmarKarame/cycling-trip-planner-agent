from src.models import (
    AccommodationInput,
    ElevationInput,
    RouteInput,
    WeatherInput,
)
from src.tools import ToolRegistry

# Each definition pairs a tool name with its description and Pydantic input model.
_CORE_TOOLS = [
    {
        "name": "get_route",
        "description": (
            "Get a cycling route between two locations. Returns total distance, "
            "estimated number of days, and waypoints along the route. "
            "Use this FIRST before any other tools to establish the route framework."
        ),
        "input_schema": RouteInput.model_json_schema(),
    },
    {
        "name": "find_accommodation",
        "description": (
            "Find places to stay near a location along the cycling route. "
            "Returns camping, hostel, and hotel options with prices and ratings. "
            "Use AFTER get_route to find stays at waypoints."
        ),
        "input_schema": AccommodationInput.model_json_schema(),
    },
    {
        "name": "get_weather",
        "description": (
            "Get typical weather conditions for a location in a given month. "
            "Returns average temperature, rain chance, wind speed, and a summary. "
            "Useful for advising on clothing and gear."
        ),
        "input_schema": WeatherInput.model_json_schema(),
    },
    {
        "name": "get_elevation_profile",
        "description": (
            "Get the terrain difficulty between two locations. "
            "Returns total elevation gain, maximum elevation, and a difficulty rating. "
            "Use AFTER get_route to assess how challenging each segment will be."
        ),
        "input_schema": ElevationInput.model_json_schema(),
    },
]


def get_tool_definitions(registry: ToolRegistry) -> list[dict]:
    """Return tool definitions for only the tools that are registered.

    This ensures Claude only sees tools that have a backing implementation.
    """
    available = {
        "get_route": registry.route,
        "find_accommodation": registry.accommodation,
        "get_weather": registry.weather,
        "get_elevation_profile": registry.elevation,
    }

    return [
        tool for tool in _CORE_TOOLS if available.get(tool["name"]) is not None
    ]
