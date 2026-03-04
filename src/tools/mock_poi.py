import hashlib

from src.models import POICategory, POIInput, POIOutput, PointOfInterest

# Realistic POIs for locations commonly found on European cycling routes.
# When a location isn't in the database, we fall back to generic but
# plausible entries that don't just repeat the city name.
_LOCATION_POIS: dict[str, list[dict]] = {
    "london": [
        {
            "name": "St Paul's Cathedral",
            "category": POICategory.HISTORICAL,
            "description": "Iconic 17th-century cathedral designed by Sir Christopher Wren.",
            "latitude": 51.5138,
            "longitude": -0.0984,
            "detour_km": 0.5,
        },
        {
            "name": "Borough Market",
            "category": POICategory.FOOD,
            "description": "One of London's oldest and most renowned food markets.",
            "latitude": 51.5055,
            "longitude": -0.0910,
            "detour_km": 1.0,
        },
        {
            "name": "Greenwich Park",
            "category": POICategory.NATURE,
            "description": "Royal park with panoramic views of the Thames and Canary Wharf.",
            "latitude": 51.4769,
            "longitude": -0.0005,
            "detour_km": 3.0,
        },
        {
            "name": "Tower of London",
            "category": POICategory.HISTORICAL,
            "description": "Historic castle and fortress on the north bank of the Thames.",
            "latitude": 51.5081,
            "longitude": -0.0759,
            "detour_km": 1.5,
        },
        {
            "name": "Primrose Hill Viewpoint",
            "category": POICategory.VIEWPOINT,
            "description": "Hill offering sweeping views across central London's skyline.",
            "latitude": 51.5390,
            "longitude": -0.1603,
            "detour_km": 4.0,
        },
    ],
    "paris": [
        {
            "name": "Notre-Dame de Paris",
            "category": POICategory.HISTORICAL,
            "description": "Medieval Catholic cathedral on the Île de la Cité.",
            "latitude": 48.8530,
            "longitude": 2.3499,
            "detour_km": 0.5,
        },
        {
            "name": "Marché des Enfants Rouges",
            "category": POICategory.FOOD,
            "description": "The oldest covered market in Paris, dating back to 1615.",
            "latitude": 48.8630,
            "longitude": 2.3627,
            "detour_km": 1.5,
        },
        {
            "name": "Bois de Vincennes",
            "category": POICategory.NATURE,
            "description": "Large public park on the eastern edge of Paris with cycling paths.",
            "latitude": 48.8283,
            "longitude": 2.4330,
            "detour_km": 5.0,
        },
        {
            "name": "Sacré-Cœur Basilica Viewpoint",
            "category": POICategory.VIEWPOINT,
            "description": "Hilltop basilica in Montmartre with panoramic city views.",
            "latitude": 48.8867,
            "longitude": 2.3431,
            "detour_km": 3.0,
        },
        {
            "name": "Musée d'Orsay",
            "category": POICategory.CULTURAL,
            "description": "Art museum in a former railway station, housing Impressionist masterpieces.",
            "latitude": 48.8600,
            "longitude": 2.3266,
            "detour_km": 1.0,
        },
    ],
    "brussels": [
        {
            "name": "Cathedral of St. Michael and St. Gudula",
            "category": POICategory.HISTORICAL,
            "description": "Gothic cathedral dating from the 13th century in the heart of Brussels.",
            "latitude": 50.8483,
            "longitude": 4.3601,
            "detour_km": 0.5,
        },
        {
            "name": "Grand Place",
            "category": POICategory.CULTURAL,
            "description": "UNESCO World Heritage central square surrounded by ornate guild halls.",
            "latitude": 50.8467,
            "longitude": 4.3525,
            "detour_km": 0.5,
        },
        {
            "name": "Forêt de Soignes",
            "category": POICategory.NATURE,
            "description": "Ancient beech forest on the edge of Brussels, great for cycling detours.",
            "latitude": 50.7750,
            "longitude": 4.4167,
            "detour_km": 5.0,
        },
        {
            "name": "Delirium Café & Belgian Beer District",
            "category": POICategory.FOOD,
            "description": "Famous area for sampling Belgian beers and traditional moules-frites.",
            "latitude": 50.8481,
            "longitude": 4.3548,
            "detour_km": 1.0,
        },
        {
            "name": "Mont des Arts Viewpoint",
            "category": POICategory.VIEWPOINT,
            "description": "Garden terrace with views over the Brussels skyline and lower town.",
            "latitude": 50.8445,
            "longitude": 4.3570,
            "detour_km": 1.0,
        },
    ],
    "cologne": [
        {
            "name": "Cologne Cathedral (Kölner Dom)",
            "category": POICategory.HISTORICAL,
            "description": "UNESCO-listed Gothic masterpiece and Germany's most visited landmark.",
            "latitude": 50.9413,
            "longitude": 6.9583,
            "detour_km": 0.5,
        },
        {
            "name": "Rheinpark",
            "category": POICategory.NATURE,
            "description": "Riverside park along the Rhine with cycling paths and cable-car views.",
            "latitude": 50.9462,
            "longitude": 6.9750,
            "detour_km": 2.0,
        },
        {
            "name": "Brauhaus Früh am Dom",
            "category": POICategory.FOOD,
            "description": "Traditional brewery serving Kölsch beer and hearty Rhineland cuisine.",
            "latitude": 50.9400,
            "longitude": 6.9563,
            "detour_km": 0.5,
        },
        {
            "name": "Hohenzollern Bridge Viewpoint",
            "category": POICategory.VIEWPOINT,
            "description": "Pedestrian bridge over the Rhine with iconic views of the cathedral.",
            "latitude": 50.9414,
            "longitude": 6.9649,
            "detour_km": 1.0,
        },
        {
            "name": "Museum Ludwig",
            "category": POICategory.CULTURAL,
            "description": "Major modern art museum with works by Warhol, Picasso, and Lichtenstein.",
            "latitude": 50.9408,
            "longitude": 6.9614,
            "detour_km": 0.5,
        },
    ],
    "zurich": [
        {
            "name": "Grossmünster",
            "category": POICategory.HISTORICAL,
            "description": "Romanesque Protestant church, a landmark of Zurich since the 12th century.",
            "latitude": 47.3700,
            "longitude": 8.5440,
            "detour_km": 0.5,
        },
        {
            "name": "Lindenhof Viewpoint",
            "category": POICategory.VIEWPOINT,
            "description": "Hilltop square in the old town with views over the Limmat river and Alps.",
            "latitude": 47.3726,
            "longitude": 8.5410,
            "detour_km": 0.5,
        },
        {
            "name": "Zürichsee Lakeside Path",
            "category": POICategory.NATURE,
            "description": "Scenic lakeside promenade ideal for a relaxing post-ride stroll.",
            "latitude": 47.3532,
            "longitude": 8.5414,
            "detour_km": 2.0,
        },
        {
            "name": "Zeughauskeller",
            "category": POICategory.FOOD,
            "description": "Historic armoury turned restaurant serving Swiss classics since 1487.",
            "latitude": 47.3717,
            "longitude": 8.5396,
            "detour_km": 0.5,
        },
        {
            "name": "Swiss National Museum",
            "category": POICategory.CULTURAL,
            "description": "Comprehensive museum of Swiss cultural history near the main station.",
            "latitude": 47.3793,
            "longitude": 8.5397,
            "detour_km": 1.0,
        },
    ],
    "amsterdam": [
        {
            "name": "Rijksmuseum",
            "category": POICategory.CULTURAL,
            "description": "World-famous museum housing Rembrandt's Night Watch and Dutch masters.",
            "latitude": 52.3600,
            "longitude": 4.8852,
            "detour_km": 1.0,
        },
        {
            "name": "Vondelpark",
            "category": POICategory.NATURE,
            "description": "Amsterdam's most popular park with cycling paths and open-air theatre.",
            "latitude": 52.3579,
            "longitude": 4.8686,
            "detour_km": 1.5,
        },
        {
            "name": "Albert Cuyp Market",
            "category": POICategory.FOOD,
            "description": "The largest daily street market in the Netherlands with Dutch treats.",
            "latitude": 52.3557,
            "longitude": 4.8939,
            "detour_km": 1.0,
        },
        {
            "name": "Westerkerk Tower Viewpoint",
            "category": POICategory.VIEWPOINT,
            "description": "Climb the tallest church tower in Amsterdam for canal-district views.",
            "latitude": 52.3745,
            "longitude": 4.8839,
            "detour_km": 2.0,
        },
        {
            "name": "Anne Frank House",
            "category": POICategory.HISTORICAL,
            "description": "The preserved hiding place of Anne Frank, now a moving museum.",
            "latitude": 52.3752,
            "longitude": 4.8840,
            "detour_km": 2.0,
        },
    ],
    "strasbourg": [
        {
            "name": "Strasbourg Cathedral",
            "category": POICategory.HISTORICAL,
            "description": "Gothic cathedral with an astronomical clock and panoramic platform.",
            "latitude": 48.5818,
            "longitude": 7.7510,
            "detour_km": 0.5,
        },
        {
            "name": "Petite France Quarter",
            "category": POICategory.CULTURAL,
            "description": "Picturesque canal-side district with half-timbered Alsatian houses.",
            "latitude": 48.5800,
            "longitude": 7.7400,
            "detour_km": 1.0,
        },
        {
            "name": "Parc de l'Orangerie",
            "category": POICategory.NATURE,
            "description": "Oldest park in Strasbourg with a lake, zoo, and shaded cycling paths.",
            "latitude": 48.5880,
            "longitude": 7.7680,
            "detour_km": 2.0,
        },
        {
            "name": "Alsatian Winstub District",
            "category": POICategory.FOOD,
            "description": "Traditional Alsatian wine taverns serving tarte flambée and local wines.",
            "latitude": 48.5810,
            "longitude": 7.7490,
            "detour_km": 0.5,
        },
        {
            "name": "Barrage Vauban Viewpoint",
            "category": POICategory.VIEWPOINT,
            "description": "Covered bridge with a rooftop terrace overlooking the Petite France quarter.",
            "latitude": 48.5793,
            "longitude": 7.7370,
            "detour_km": 1.0,
        },
    ],
    "basel": [
        {
            "name": "Basel Minster",
            "category": POICategory.HISTORICAL,
            "description": "Red sandstone cathedral on a hill above the Rhine with a Gothic cloister.",
            "latitude": 47.5560,
            "longitude": 7.5920,
            "detour_km": 0.5,
        },
        {
            "name": "Münsterplatz Viewpoint",
            "category": POICategory.VIEWPOINT,
            "description": "Terrace behind the Minster with views over the Rhine into Germany and France.",
            "latitude": 47.5565,
            "longitude": 7.5930,
            "detour_km": 0.5,
        },
        {
            "name": "Markthalle Basel",
            "category": POICategory.FOOD,
            "description": "Indoor food hall with international and Swiss street food stalls.",
            "latitude": 47.5480,
            "longitude": 7.5890,
            "detour_km": 1.0,
        },
        {
            "name": "Fondation Beyeler",
            "category": POICategory.CULTURAL,
            "description": "World-class modern art museum set in a Renzo Piano building with gardens.",
            "latitude": 47.5910,
            "longitude": 7.5970,
            "detour_km": 5.0,
        },
        {
            "name": "Rhine Swimming & Promenade",
            "category": POICategory.NATURE,
            "description": "Popular stretch for swimming in the Rhine current — a Basel tradition.",
            "latitude": 47.5590,
            "longitude": 7.5880,
            "detour_km": 1.5,
        },
    ],
}

# Fallback templates for locations not in the database.
# These use region-appropriate generic names instead of "{location} Cathedral".
_FALLBACK_TEMPLATES = [
    {
        "suffix": "Old Town Square",
        "category": POICategory.HISTORICAL,
        "description": "Historic town centre with charming architecture and local shops.",
        "detour_km": 0.5,
    },
    {
        "suffix": "Riverside Trail",
        "category": POICategory.NATURE,
        "description": "Scenic riverside path popular with cyclists and walkers.",
        "detour_km": 2.0,
    },
    {
        "suffix": "Farmers' Market",
        "category": POICategory.FOOD,
        "description": "Weekly market selling regional produce, cheeses, and baked goods.",
        "detour_km": 1.0,
    },
    {
        "suffix": "Church Tower Viewpoint",
        "category": POICategory.VIEWPOINT,
        "description": "Climb the local church tower for views over the surrounding countryside.",
        "detour_km": 1.5,
    },
    {
        "suffix": "Regional Heritage Museum",
        "category": POICategory.CULTURAL,
        "description": "Small museum covering local history, crafts, and traditions.",
        "detour_km": 1.0,
    },
]


class MockPOIProvider:
    """Mock POI provider that returns realistic points of interest."""

    def get_points_of_interest(self, input: POIInput) -> POIOutput:
        loc = input.location
        loc_key = loc.lower().strip()

        if loc_key in _LOCATION_POIS:
            pois = [
                PointOfInterest(**poi)
                for poi in _LOCATION_POIS[loc_key]
                if poi["detour_km"] <= input.radius_km
            ]
        else:
            # Fallback: generate plausible generic POIs
            seed = int(hashlib.md5(loc.encode()).hexdigest()[:8], 16)
            base_lat = 48.0 + (seed % 100) / 20.0
            base_lon = 2.0 + (seed % 80) / 10.0

            pois = []
            for i, template in enumerate(_FALLBACK_TEMPLATES):
                if template["detour_km"] > input.radius_km:
                    continue
                pois.append(
                    PointOfInterest(
                        name=f"{loc} {template['suffix']}",
                        category=template["category"],
                        description=template["description"],
                        latitude=base_lat + (i * 0.01),
                        longitude=base_lon + (i * 0.015),
                        detour_km=template["detour_km"],
                    )
                )

        return POIOutput(location=loc, points_of_interest=pois)
