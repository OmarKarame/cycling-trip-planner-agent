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
    # ─── UK routes ────────────────────────────────────────────
    ("london", "edinburgh"): (
        660.0,
        [
            ("London", 51.5074, -0.1278),
            ("Cambridge", 52.2053, 0.1218),
            ("Peterborough", 52.5695, -0.2405),
            ("Lincoln", 53.2307, -0.5406),
            ("York", 53.9591, -1.0815),
            ("Durham", 54.7761, -1.5733),
            ("Newcastle", 54.9783, -1.6178),
            ("Berwick-upon-Tweed", 55.7710, -2.0015),
            ("Edinburgh", 55.9533, -3.1883),
        ],
    ),
    ("london", "bristol"): (
        190.0,
        [
            ("London", 51.5074, -0.1278),
            ("Reading", 51.4543, -0.9781),
            ("Swindon", 51.5558, -1.7797),
            ("Bath", 51.3811, -2.3590),
            ("Bristol", 51.4545, -2.5879),
        ],
    ),
    ("london", "brighton"): (
        90.0,
        [
            ("London", 51.5074, -0.1278),
            ("Croydon", 51.3762, -0.0982),
            ("Crawley", 51.1092, -0.1872),
            ("Brighton", 50.8225, -0.1372),
        ],
    ),
    ("edinburgh", "inverness"): (
        255.0,
        [
            ("Edinburgh", 55.9533, -3.1883),
            ("Perth", 56.3952, -3.4372),
            ("Pitlochry", 56.7054, -3.7341),
            ("Aviemore", 57.1953, -3.8258),
            ("Inverness", 57.4778, -4.2247),
        ],
    ),
    # ─── More European routes ─────────────────────────────────
    ("london", "paris"): (
        460.0,
        [
            ("London", 51.5074, -0.1278),
            ("Canterbury", 51.2802, 1.0789),
            ("Dover", 51.1279, 1.3134),
            ("Calais", 50.9513, 1.8587),
            ("Amiens", 49.8942, 2.2957),
            ("Paris", 48.8566, 2.3522),
        ],
    ),
    ("rome", "florence"): (
        280.0,
        [
            ("Rome", 41.9028, 12.4964),
            ("Orvieto", 42.7186, 12.1107),
            ("Siena", 43.3188, 11.3308),
            ("Florence", 43.7696, 11.2558),
        ],
    ),
    ("barcelona", "valencia"): (
        350.0,
        [
            ("Barcelona", 41.3874, 2.1686),
            ("Tarragona", 41.1189, 1.2445),
            ("Tortosa", 40.8125, 0.5216),
            ("Castellón", 39.9864, -0.0513),
            ("Valencia", 39.4699, -0.3763),
        ],
    ),
    ("lisbon", "porto"): (
        315.0,
        [
            ("Lisbon", 38.7223, -9.1393),
            ("Santarém", 39.2369, -8.6870),
            ("Coimbra", 40.2033, -8.4103),
            ("Aveiro", 40.6405, -8.6538),
            ("Porto", 41.1579, -8.6291),
        ],
    ),
    ("munich", "vienna"): (
        430.0,
        [
            ("Munich", 48.1351, 11.5820),
            ("Rosenheim", 47.8561, 12.1289),
            ("Salzburg", 47.8095, 13.0550),
            ("Linz", 48.3069, 14.2858),
            ("Melk", 48.2274, 15.3320),
            ("Vienna", 48.2082, 16.3738),
        ],
    ),
    ("london", "amsterdam"): (
        520.0,
        [
            ("London", 51.5074, -0.1278),
            ("Canterbury", 51.2802, 1.0789),
            ("Dover", 51.1279, 1.3134),
            ("Calais", 50.9513, 1.8587),
            ("Dunkirk", 51.0343, 2.3768),
            ("Bruges", 51.2093, 3.2247),
            ("Ghent", 51.0543, 3.7174),
            ("Antwerp", 51.2194, 4.4025),
            ("Breda", 51.5719, 4.7683),
            ("Rotterdam", 51.9244, 4.4777),
            ("Amsterdam", 52.3676, 4.9041),
        ],
    ),
    ("london", "zurich"): (
        950.0,
        [
            ("London", 51.5074, -0.1278),
            ("Dover", 51.1279, 1.3134),
            ("Calais", 50.9513, 1.8587),
            ("Lille", 50.6292, 3.0573),
            ("Brussels", 50.8503, 4.3517),
            ("Luxembourg City", 49.6117, 6.1300),
            ("Metz", 49.1193, 6.1757),
            ("Strasbourg", 48.5734, 7.7521),
            ("Colmar", 48.0794, 7.3558),
            ("Basel", 47.5596, 7.5886),
            ("Zurich", 47.3769, 8.5417),
        ],
    ),
}

# Coordinates for common cities, used by the fallback route generator
# so that start/end points appear in the correct map location.
_CITY_COORDS: dict[str, tuple[float, float]] = {
    "london": (51.5074, -0.1278),
    "paris": (48.8566, 2.3522),
    "amsterdam": (52.3676, 4.9041),
    "brussels": (50.8503, 4.3517),
    "berlin": (52.5200, 13.4050),
    "copenhagen": (55.6761, 12.5683),
    "prague": (50.0755, 14.4378),
    "vienna": (48.2082, 16.3738),
    "munich": (48.1351, 11.5820),
    "zurich": (47.3769, 8.5417),
    "rome": (41.9028, 12.4964),
    "florence": (43.7696, 11.2558),
    "barcelona": (41.3874, 2.1686),
    "valencia": (39.4699, -0.3763),
    "lisbon": (38.7223, -9.1393),
    "porto": (41.1579, -8.6291),
    "edinburgh": (55.9533, -3.1883),
    "inverness": (57.4778, -4.2247),
    "brighton": (50.8225, -0.1372),
    "bristol": (51.4545, -2.5879),
    "hamburg": (53.5511, 9.9937),
    "cologne": (50.9375, 6.9603),
    "strasbourg": (48.5734, 7.7521),
    "basel": (47.5596, 7.5886),
    "lyon": (45.7640, 4.8357),
    "geneva": (46.2044, 6.1432),
    "milan": (45.4642, 9.1900),
    "dublin": (53.3498, -6.2603),
    "salzburg": (47.8095, 13.0550),
    "nice": (43.7102, 7.2620),
    "marseille": (43.2965, 5.3698),
    "madrid": (40.4168, -3.7038),
    "oslo": (59.9139, 10.7522),
    "stockholm": (59.3293, 18.0686),
    "budapest": (47.4979, 19.0402),
    "warsaw": (52.2297, 21.0122),
    "krakow": (50.0647, 19.9450),
}


def _generate_fallback_waypoints(
    start: str, end: str, num_days: int
) -> list[tuple[str, float, float]]:
    """Generate synthetic waypoints for unknown routes.

    Uses real coordinates for known cities when available, so the map
    at least shows start/end in the correct locations.
    """
    start_lat, start_lon = _CITY_COORDS.get(
        start.lower().strip(), (50.0, 5.0)
    )
    end_lat, end_lon = _CITY_COORDS.get(
        end.lower().strip(), (52.0, 10.0)
    )

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
