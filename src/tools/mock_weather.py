from src.models import WeatherInput, WeatherOutput

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


class MockWeatherProvider:
    def get_weather(self, input: WeatherInput) -> WeatherOutput:
        season = _MONTH_TO_SEASON[input.month]
        temp, rain, wind, summary = _SEASONAL_DATA[season]

        return WeatherOutput(
            location=input.location,
            month=input.month,
            avg_temp_celsius=temp,
            rain_chance_percent=rain,
            wind_speed_kmh=wind,
            summary=f"{input.location} in month {input.month}: {summary}",
        )
