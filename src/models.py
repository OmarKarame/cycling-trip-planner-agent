from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


# ─── Enums ────────────────────────────────────────────────────


class DifficultyRating(str, Enum):
    EASY = "easy"
    MODERATE = "moderate"
    HARD = "hard"
    EXTREME = "extreme"


class AccommodationType(str, Enum):
    CAMPING = "camping"
    HOSTEL = "hostel"
    HOTEL = "hotel"


# ─── Route ────────────────────────────────────────────────────


class Waypoint(BaseModel):
    name: str
    latitude: float
    longitude: float
    day: int = Field(description="Which day of the trip this waypoint falls on")


class RouteInput(BaseModel):
    start: str = Field(description="Starting location name")
    end: str = Field(description="Ending location name")
    daily_distance_km: float = Field(
        default=100.0, description="Target daily cycling distance in km"
    )


class RouteOutput(BaseModel):
    start: str
    end: str
    total_distance_km: float
    estimated_days: int
    waypoints: list[Waypoint]


# ─── Accommodation ────────────────────────────────────────────


class Accommodation(BaseModel):
    name: str
    type: AccommodationType
    price_per_night: float
    rating: float = Field(ge=0, le=5)
    location: str


class AccommodationInput(BaseModel):
    location: str = Field(description="Location to search near")
    accommodation_type: Optional[AccommodationType] = Field(
        default=None, description="Filter by type; if None, return all types"
    )
    max_price: Optional[float] = Field(
        default=None, description="Maximum price per night"
    )


class AccommodationOutput(BaseModel):
    location: str
    accommodations: list[Accommodation]


# ─── Weather ──────────────────────────────────────────────────


class WeatherInput(BaseModel):
    location: str = Field(description="Location to check weather for")
    month: int = Field(ge=1, le=12, description="Month number (1-12)")
    days: Optional[int] = Field(
        default=None,
        ge=1,
        description=(
            "Number of trip days to generate daily forecasts for. "
            "When provided, returns a daily_forecasts list with per-day weather."
        ),
    )


class DailyForecast(BaseModel):
    day: int = Field(description="Day number of the trip (1-based)")
    avg_temp_celsius: float
    rain_chance_percent: float
    wind_speed_kmh: float
    summary: str


class WeatherOutput(BaseModel):
    location: str
    month: int
    avg_temp_celsius: float
    rain_chance_percent: float
    wind_speed_kmh: float
    summary: str
    daily_forecasts: Optional[list[DailyForecast]] = Field(
        default=None,
        description="Per-day weather forecasts when days parameter was provided",
    )


# ─── Elevation ────────────────────────────────────────────────


class ElevationInput(BaseModel):
    start: str = Field(description="Starting location")
    end: str = Field(description="Ending location")


class ElevationOutput(BaseModel):
    start: str
    end: str
    total_elevation_gain_m: float
    max_elevation_m: float
    difficulty: DifficultyRating


# ─── Points of Interest ──────────────────────────────────────


class POICategory(str, Enum):
    HISTORICAL = "historical"
    NATURE = "nature"
    FOOD = "food"
    VIEWPOINT = "viewpoint"
    CULTURAL = "cultural"


class PointOfInterest(BaseModel):
    name: str
    category: POICategory
    description: str
    latitude: float
    longitude: float
    detour_km: float = Field(description="Extra km to visit this POI")


class POIInput(BaseModel):
    location: str = Field(description="Location to search near")
    radius_km: float = Field(default=20.0, description="Search radius in km")


class POIOutput(BaseModel):
    location: str
    points_of_interest: list[PointOfInterest]


# ─── Visa Requirements ───────────────────────────────────────


class VisaRequirement(BaseModel):
    country: str
    visa_required: bool
    visa_type: Optional[str] = None
    notes: str


class VisaInput(BaseModel):
    nationality: str = Field(description="Traveller's nationality/passport country")
    countries: list[str] = Field(description="Countries the route passes through")


class VisaOutput(BaseModel):
    nationality: str
    requirements: list[VisaRequirement]


# ─── Budget Estimation ───────────────────────────────────────


class BudgetBreakdown(BaseModel):
    accommodation: float
    food: float
    transport: float = Field(description="Bike maintenance, ferries, trains etc.")
    activities: float
    total: float


class BudgetInput(BaseModel):
    start: str = Field(description="Starting location")
    end: str = Field(description="Ending location")
    days: int = Field(description="Number of trip days")
    accommodation_type: AccommodationType = Field(default=AccommodationType.HOSTEL)
    budget_level: str = Field(
        default="moderate", description="Budget level: budget, moderate, or comfort"
    )


class BudgetOutput(BaseModel):
    daily_estimate: BudgetBreakdown
    total_estimate: BudgetBreakdown
    currency: str = "EUR"
    tips: list[str]


# ─── API Request / Response ───────────────────────────────────


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    response: str
    tools_used: list[str] = Field(default_factory=list)
    trip_data: Optional[dict] = None
