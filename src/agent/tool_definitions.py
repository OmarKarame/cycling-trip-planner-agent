from src.models import (
    AccommodationInput,
    BudgetInput,
    ElevationInput,
    POIInput,
    RouteInput,
    VisaInput,
    WeatherInput,
)
from src.tools import ToolRegistry

# Each definition pairs a tool name with its description and Pydantic input model.
_ALL_TOOLS = [
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
            "When the 'days' parameter is provided, also returns daily_forecasts "
            "with per-day weather for the trip duration. Use the 'days' parameter "
            "after calling get_route so you can include weather for each day of the trip."
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
    {
        "name": "get_points_of_interest",
        "description": (
            "Find interesting places to visit near a location along the cycling route. "
            "Returns historical sites, nature spots, food markets, viewpoints, and "
            "cultural attractions with detour distances. "
            "Use AFTER get_route to suggest sightseeing stops at waypoints."
        ),
        "input_schema": POIInput.model_json_schema(),
    },
    {
        "name": "check_visa_requirements",
        "description": (
            "Check visa requirements for countries along the cycling route. "
            "Takes the traveller's nationality and list of countries the route passes "
            "through. Returns whether a visa is needed for each country and any notes. "
            "Use when the route crosses international borders."
        ),
        "input_schema": VisaInput.model_json_schema(),
    },
    {
        "name": "estimate_budget",
        "description": (
            "Estimate the total trip budget based on route, duration, accommodation "
            "preference, and budget level. Returns daily and total cost breakdowns "
            "for accommodation, food, transport, and activities, plus money-saving tips. "
            "Use AFTER get_route to give the user a cost overview."
        ),
        "input_schema": BudgetInput.model_json_schema(),
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
        "get_points_of_interest": registry.poi,
        "check_visa_requirements": registry.visa,
        "estimate_budget": registry.budget,
    }

    return [
        tool for tool in _ALL_TOOLS if available.get(tool["name"]) is not None
    ]
