import math

from src.models import DailyForecast, WeatherInput, WeatherOutput

# Seasonal weather templates: (avg_temp_c, rain_chance_%, wind_kmh, summary)
_SEASONAL_DATA: dict[str, tuple[float, float, float, str]] = {
    "winter": (2.0, 55.0, 20.0, "Cold with frequent rain or snow. Pack warm layers."),
    "spring": (12.0, 35.0, 15.0, "Mild and pleasant. Occasional showers possible."),
    "summer": (23.0, 20.0, 12.0, "Warm and mostly dry. Great cycling weather."),
    "autumn": (10.0, 45.0, 18.0, "Cool with increasing rain. Bring waterproofs."),
}

_MONTH_TO_SEASON: dict[int, str] = {
    1: "winter",
    2: "winter",
    3: "spring",
    4: "spring",
    5: "spring",
    6: "summer",
    7: "summer",
    8: "summer",
    9: "autumn",
    10: "autumn",
    11: "autumn",
    12: "winter",
}

# Daily weather condition descriptions for variation
_DAILY_CONDITIONS: dict[str, list[str]] = {
    "winter": [
        "Overcast with light snow",
        "Cold and clear",
        "Freezing rain expected",
        "Cloudy with sleet",
        "Partly cloudy, cold winds",
    ],
    "spring": [
        "Sunny with light breeze",
        "Partly cloudy, mild",
        "Morning showers clearing",
        "Warm and sunny",
        "Overcast with occasional drizzle",
    ],
    "summer": [
        "Sunny and warm",
        "Clear skies, hot",
        "Partly cloudy, pleasant",
        "Warm with afternoon clouds",
        "Sunny, light breeze",
    ],
    "autumn": [
        "Overcast with light rain",
        "Cool and breezy",
        "Partly cloudy, mild",
        "Morning fog clearing",
        "Cloudy with scattered showers",
    ],
}


def _generate_daily_forecasts(
    base_temp: float,
    base_rain: float,
    base_wind: float,
    season: str,
    days: int,
) -> list[DailyForecast]:
    """Generate per-day forecasts with deterministic variation around the seasonal baseline."""
    conditions = _DAILY_CONDITIONS[season]
    forecasts = []
    for day in range(1, days + 1):
        # Deterministic variation using sine waves seeded by day number
        temp_offset = 3.0 * math.sin(day * 1.3)
        rain_offset = 10.0 * math.sin(day * 0.9 + 1.0)
        wind_offset = 4.0 * math.sin(day * 1.7 + 2.0)

        forecasts.append(
            DailyForecast(
                day=day,
                avg_temp_celsius=round(base_temp + temp_offset, 1),
                rain_chance_percent=round(
                    max(0.0, min(100.0, base_rain + rain_offset)), 1
                ),
                wind_speed_kmh=round(max(0.0, base_wind + wind_offset), 1),
                summary=conditions[(day - 1) % len(conditions)],
            )
        )
    return forecasts


class MockWeatherProvider:
    def get_weather(self, input: WeatherInput) -> WeatherOutput:
        season = _MONTH_TO_SEASON[input.month]
        temp, rain, wind, summary = _SEASONAL_DATA[season]

        daily_forecasts = None
        if input.days is not None:
            daily_forecasts = _generate_daily_forecasts(
                temp, rain, wind, season, input.days
            )

        return WeatherOutput(
            location=input.location,
            month=input.month,
            avg_temp_celsius=temp,
            rain_chance_percent=rain,
            wind_speed_kmh=wind,
            summary=f"{input.location} in month {input.month}: {summary}",
            daily_forecasts=daily_forecasts,
        )
