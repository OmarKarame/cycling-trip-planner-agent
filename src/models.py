from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DifficultyRating(str, Enum):
    EASY = "easy"
    MODERATE = "moderate"
    HARD = "hard"
    EXTREME = "extreme"

class AccommodationType(str, Enum):
    CAMPING = "camping"
    HOSTEL = "hostel"
    HOTEL = "hotel"




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


class WeatherOutput(BaseModel):
    location: str
    month: int
    avg_temp_celsius: float
    rain_chance_percent: float
    wind_speed_kmh: float
    summary: str


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


# ─── API Request / Response ───────────────────────────────────


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    response: str
    tools_used: list[str] = []
