from src.models import AccommodationType, BudgetBreakdown, BudgetInput, BudgetOutput

# Daily cost templates by budget level (EUR)
_DAILY_COSTS = {
    "budget": {
        AccommodationType.CAMPING: {"accommodation": 15, "food": 20, "transport": 5, "activities": 5},
        AccommodationType.HOSTEL: {"accommodation": 30, "food": 25, "transport": 5, "activities": 5},
        AccommodationType.HOTEL: {"accommodation": 60, "food": 25, "transport": 5, "activities": 5},
    },
    "moderate": {
        AccommodationType.CAMPING: {"accommodation": 20, "food": 30, "transport": 8, "activities": 10},
        AccommodationType.HOSTEL: {"accommodation": 40, "food": 35, "transport": 8, "activities": 10},
        AccommodationType.HOTEL: {"accommodation": 90, "food": 35, "transport": 8, "activities": 10},
    },
    "comfort": {
        AccommodationType.CAMPING: {"accommodation": 30, "food": 45, "transport": 12, "activities": 20},
        AccommodationType.HOSTEL: {"accommodation": 55, "food": 50, "transport": 12, "activities": 20},
        AccommodationType.HOTEL: {"accommodation": 140, "food": 50, "transport": 12, "activities": 20},
    },
}

_TIPS = {
    "budget": [
        "Cook your own meals using local supermarkets to save on food costs.",
        "Free camping (wild camping) is legal in Scandinavian countries.",
        "Carry a basic bike repair kit to avoid mechanic costs on the road.",
        "Use free water refill points at public fountains and cafés.",
    ],
    "moderate": [
        "Book hostels in advance during peak season for better rates.",
        "Mix restaurant meals with self-catering for a balanced budget.",
        "Consider a bike insurance policy for peace of mind on longer trips.",
        "Look for cyclist-friendly accommodations that offer secure bike storage.",
    ],
    "comfort": [
        "Book hotels with bike-friendly amenities (storage, wash station).",
        "Consider luggage transfer services between overnight stops.",
        "Reserve restaurant tables in advance at popular stops.",
        "Travel insurance with bike coverage is recommended for premium trips.",
    ],
}


class MockBudgetProvider:
    """Mock budget provider with cost templates by level and accommodation type."""

    def estimate_budget(self, input: BudgetInput) -> BudgetOutput:
        level = input.budget_level.lower().strip()
        if level not in _DAILY_COSTS:
            level = "moderate"

        costs = _DAILY_COSTS[level][input.accommodation_type]

        daily = BudgetBreakdown(
            accommodation=costs["accommodation"],
            food=costs["food"],
            transport=costs["transport"],
            activities=costs["activities"],
            total=sum(costs.values()),
        )

        total = BudgetBreakdown(
            accommodation=costs["accommodation"] * input.days,
            food=costs["food"] * input.days,
            transport=costs["transport"] * input.days,
            activities=costs["activities"] * input.days,
            total=sum(costs.values()) * input.days,
        )

        return BudgetOutput(
            daily_estimate=daily,
            total_estimate=total,
            currency="EUR",
            tips=_TIPS.get(level, _TIPS["moderate"]),
        )
