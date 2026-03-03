import math

from src.models import RouteInput, RouteOutput, Waypoint

# Pre-built routes for common European cycling city pairs.
# Each entry maps (start_lower, end_lower) to (distance_km, waypoints_data).
# Waypoints are (name, lat, lon) tuples — day numbers are computed at runtime.
_KNOWN_ROUTES: dict[tuple[str, str], tuple[float, list[tuple[str, float, float]]]] = {
    ("amsterdam", "copenhagen"): (
        810.0,
        [
            ("Amsterdam", 52.3676, 4.9041),
            ("Amersfoort", 52.1561, 5.3878),
            ("Zwolle", 52.5168, 6.0830),
            ("Emmen", 52.7792, 6.8936),
            ("Bremen", 53.0793, 8.8017),
            ("Hamburg", 53.5511, 9.9937),
            ("Lübeck", 53.8655, 10.6866),
            ("Fehmarn", 54.4440, 11.1977),
            ("Rødby", 54.6561, 11.3862),
            ("Copenhagen", 55.6761, 12.5683),
        ],
    ),
    ("paris", "amsterdam"): (
        505.0,
        [
            ("Paris", 48.8566, 2.3522),
            ("Compiègne", 49.4178, 2.8262),
            ("Saint-Quentin", 49.8487, 3.2876),
            ("Mons", 50.4542, 3.9563),
            ("Brussels", 50.8503, 4.3517),
            ("Antwerp", 51.2194, 4.4025),
            ("Breda", 51.5719, 4.7683),
            ("Amsterdam", 52.3676, 4.9041),
        ],
    ),
    ("berlin", "prague"): (
        350.0,
        [
            ("Berlin", 52.5200, 13.4050),
            ("Dresden", 51.0504, 13.7373),
            ("Ústí nad Labem", 50.6611, 14.0531),
            ("Prague", 50.0755, 14.4378),
        ],
    ),
}


def _generate_fallback_waypoints(
    start: str, end: str, num_days: int
) -> list[tuple[str, float, float]]:
    """Generate synthetic waypoints for unknown routes."""
    # Use simple linear interpolation between two made-up coordinates
    start_lat, start_lon = 50.0, 5.0
    end_lat, end_lon = 52.0, 10.0

    waypoints = []
    for i in range(num_days + 1):
        fraction = i / max(num_days, 1)
        lat = start_lat + (end_lat - start_lat) * fraction
        lon = start_lon + (end_lon - start_lon) * fraction
        if i == 0:
            name = start
        elif i == num_days:
            name = end
        else:
            name = f"Waypoint {i}"
        waypoints.append((name, round(lat, 4), round(lon, 4)))
    return waypoints


class MockRouteProvider:
    def get_route(self, input: RouteInput) -> RouteOutput:
        key = (input.start.lower().strip(), input.end.lower().strip())
        reverse_key = (key[1], key[0])

        if key in _KNOWN_ROUTES:
            distance, wp_data = _KNOWN_ROUTES[key]
        elif reverse_key in _KNOWN_ROUTES:
            distance, wp_data = _KNOWN_ROUTES[reverse_key]
            wp_data = list(reversed(wp_data))
        else:
            # Fallback: estimate ~400km for unknown routes
            distance = 400.0
            num_days = max(1, math.ceil(distance / input.daily_distance_km))
            wp_data = _generate_fallback_waypoints(input.start, input.end, num_days)

        num_days = max(1, math.ceil(distance / input.daily_distance_km))

        waypoints = []
        for i, (name, lat, lon) in enumerate(wp_data):
            day = min(max(1, round(i * num_days / max(len(wp_data) - 1, 1))), num_days)
            if i == 0:
                day = 1
            waypoints.append(Waypoint(name=name, latitude=lat, longitude=lon, day=day))

        return RouteOutput(
            start=input.start,
            end=input.end,
            total_distance_km=distance,
            estimated_days=num_days,
            waypoints=waypoints,
        )
