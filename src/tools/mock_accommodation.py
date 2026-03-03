from src.models import (
    Accommodation,
    AccommodationInput,
    AccommodationOutput,
    AccommodationType,
)

# Template accommodations per type. The location field is filled at runtime.
_TEMPLATES: dict[AccommodationType, list[tuple[str, float, float]]] = {
    AccommodationType.CAMPING: [
        ("Riverside Campsite", 12.0, 3.8),
        ("Green Meadows Camping", 15.0, 4.0),
        ("Lakeside Camp", 18.0, 4.2),
    ],
    AccommodationType.HOSTEL: [
        ("Backpackers Hub", 28.0, 4.1),
        ("City Centre Hostel", 35.0, 4.3),
        ("Wanderer's Rest", 42.0, 4.5),
    ],
    AccommodationType.HOTEL: [
        ("Comfort Inn", 75.0, 3.9),
        ("Park View Hotel", 95.0, 4.2),
        ("Grand Cycling Hotel", 120.0, 4.6),
    ],
}


class MockAccommodationProvider:
    def find_accommodation(self, input: AccommodationInput) -> AccommodationOutput:
        results: list[Accommodation] = []

        if input.accommodation_type is not None:
            types_to_search = [input.accommodation_type]
        else:
            types_to_search = list(AccommodationType)

        for acc_type in types_to_search:
            for name, price, rating in _TEMPLATES.get(acc_type, []):
                if input.max_price is not None and price > input.max_price:
                    continue
                results.append(
                    Accommodation(
                        name=f"{name} — {input.location}",
                        type=acc_type,
                        price_per_night=price,
                        rating=rating,
                        location=input.location,
                    )
                )

        return AccommodationOutput(
            location=input.location,
            accommodations=results,
        )
