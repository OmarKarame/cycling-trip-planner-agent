from src.models import DifficultyRating, ElevationInput, ElevationOutput

# Keywords that suggest mountainous terrain
_HARD_KEYWORDS = {"alps", "pyrenees", "dolomites", "mountain", "sierra", "andes"}
_MODERATE_KEYWORDS = {"hill", "highland", "ardennes", "black forest", "vosges"}


def _classify_terrain(start: str, end: str) -> tuple[float, float, DifficultyRating]:
    """Return (elevation_gain_m, max_elevation_m, difficulty) based on location names."""
    combined = f"{start} {end}".lower()

    if any(kw in combined for kw in _HARD_KEYWORDS):
        return 4500.0, 2100.0, DifficultyRating.HARD

    if any(kw in combined for kw in _MODERATE_KEYWORDS):
        return 2200.0, 850.0, DifficultyRating.MODERATE

    # Default: flat to gently rolling terrain (typical Northern Europe)
    return 800.0, 120.0, DifficultyRating.EASY


class MockElevationProvider:
    def get_elevation_profile(self, input: ElevationInput) -> ElevationOutput:
        gain, max_elev, difficulty = _classify_terrain(input.start, input.end)

        return ElevationOutput(
            start=input.start,
            end=input.end,
            total_elevation_gain_m=gain,
            max_elevation_m=max_elev,
            difficulty=difficulty,
        )
