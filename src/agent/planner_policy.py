from __future__ import annotations

import re
from dataclasses import dataclass

from src.models import AccommodationType, DifficultyRating

_MONTHS = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "sept": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}

_SEASON_TO_MONTH = {
    "spring": 4,
    "summer": 7,
    "autumn": 10,
    "fall": 10,
    "winter": 1,
}


@dataclass
class PlanningSlots:
    """Structured user preferences captured from conversation and tool calls."""

    start: str | None = None
    end: str | None = None
    month: int | None = None
    travel_timing_note: str | None = None
    travel_timing_is_approximate: bool = False
    daily_distance_km: float | None = None
    budget_per_day_eur: float | None = None
    accommodation_type: AccommodationType | None = None
    accommodation_secondary_type: AccommodationType | None = None
    accommodation_secondary_every_n_nights: int | None = None
    difficulty_preference: DifficultyRating | None = None
    budget_level: str | None = None


def _normalize_location(raw: str) -> str:
    """Normalize location phrases while preserving human-readable casing."""
    cleaned = " ".join(raw.strip(" .,!?").split())
    if not cleaned:
        return ""
    return cleaned.title()


def _parse_difficulty(text: str) -> DifficultyRating | None:
    if any(word in text for word in ("beginner", "easy", "relaxed", "gentle")):
        return DifficultyRating.EASY
    if any(word in text for word in ("moderate", "intermediate", "balanced")):
        return DifficultyRating.MODERATE
    if any(word in text for word in ("hard", "challenging", "tough", "advanced")):
        return DifficultyRating.HARD
    if any(word in text for word in ("extreme", "expert", "very hard")):
        return DifficultyRating.EXTREME
    return None


def _parse_budget_per_day(text: str) -> float | None:
    explicit_per_day = re.search(
        r"(?:€|\$|£)?\s*(\d{2,4})(?:\s*(?:eur|euro|euros|usd|dollars|gbp|pounds))?\s*(?:/|per)\s*day",
        text,
    )
    if explicit_per_day:
        return float(explicit_per_day.group(1))

    budget_statement = re.search(
        r"\bbudget(?:\s+of|\s+is|\s*:)?\s*(?:€|\$|£)?\s*(\d{2,4})\b",
        text,
    )
    if budget_statement:
        return float(budget_statement.group(1))

    return None


def _parse_accommodation_type(word: str) -> AccommodationType | None:
    normalized = word.lower().strip()
    if normalized.startswith("camp"):
        return AccommodationType.CAMPING
    if normalized.startswith("hostel"):
        return AccommodationType.HOSTEL
    if normalized.startswith("hotel"):
        return AccommodationType.HOTEL
    return None


def _extract_mixed_accommodation_pattern(text: str) -> tuple[AccommodationType | None, int | None]:
    match = re.search(
        r"\b(camp(?:ing)?|hostel|hotel)s?\b\s+every\s+(\d{1,2})(?:st|nd|rd|th)?\s+night\b",
        text,
    )
    if not match:
        return None, None

    alt_type = _parse_accommodation_type(match.group(1))
    cadence = int(match.group(2))
    if cadence < 2:
        return None, None
    return alt_type, cadence


def update_slots_from_user_message(slots: PlanningSlots, message: str) -> set[str]:
    """Extract high-value planning fields from free-form user text."""
    captured: set[str] = set()
    text = message.strip()
    lower = text.lower()

    from_to = re.search(
        r"\bfrom\s+([a-z][a-z\s.'-]{1,60}?)\s+to\s+([a-z][a-z\s.'-]{1,60}?)"
        r"(?:\s+in\b|[,.!?]|$)",
        lower,
    )
    if from_to:
        start = _normalize_location(from_to.group(1))
        end = _normalize_location(from_to.group(2))
        if start:
            slots.start = start
            captured.add("start")
        if end:
            slots.end = end
            captured.add("end")

    month_match = re.search(r"\b(" + "|".join(_MONTHS.keys()) + r")\b", lower)
    if month_match:
        month_text = month_match.group(1)
        slots.month = _MONTHS[month_text]
        slots.travel_timing_note = month_text
        slots.travel_timing_is_approximate = False
        captured.add("month")
    else:
        numeric_month = re.search(r"\bmonth\s*(?:is\s*)?(1[0-2]|[1-9])\b", lower)
        if numeric_month:
            slots.month = int(numeric_month.group(1))
            slots.travel_timing_note = f"month {numeric_month.group(1)}"
            slots.travel_timing_is_approximate = False
            captured.add("month")
        else:
            season_match = re.search(r"\b(" + "|".join(_SEASON_TO_MONTH.keys()) + r")\b", lower)
            if season_match:
                season = season_match.group(1)
                slots.month = _SEASON_TO_MONTH[season]
                slots.travel_timing_note = season
                slots.travel_timing_is_approximate = True
                captured.add("month")

    distance_match = re.search(
        r"\b(?:around|about|roughly|approx(?:imately)?|~)?\s*(\d{2,3})\s*km(?:\s*(?:/|per|a)\s*day|\s+daily)\b",
        lower,
    )
    if distance_match:
        slots.daily_distance_km = float(distance_match.group(1))
        captured.add("daily_distance_km")

    budget_per_day = _parse_budget_per_day(lower)
    if budget_per_day is not None:
        slots.budget_per_day_eur = budget_per_day
        captured.add("budget_per_day_eur")

    if "prefer camp" in lower or "prefer camping" in lower:
        slots.accommodation_type = AccommodationType.CAMPING
        captured.add("accommodation_type")
    elif "prefer hostel" in lower:
        slots.accommodation_type = AccommodationType.HOSTEL
        captured.add("accommodation_type")
    elif "prefer hotel" in lower:
        slots.accommodation_type = AccommodationType.HOTEL
        captured.add("accommodation_type")
    elif "camp" in lower:
        slots.accommodation_type = AccommodationType.CAMPING
        captured.add("accommodation_type")
    elif "hostel" in lower:
        slots.accommodation_type = AccommodationType.HOSTEL
        captured.add("accommodation_type")
    elif "hotel" in lower:
        slots.accommodation_type = AccommodationType.HOTEL
        captured.add("accommodation_type")

    secondary_type, cadence = _extract_mixed_accommodation_pattern(lower)
    if secondary_type is not None and cadence is not None:
        slots.accommodation_secondary_type = secondary_type
        slots.accommodation_secondary_every_n_nights = cadence
        if slots.accommodation_type is None:
            slots.accommodation_type = secondary_type
        captured.add("accommodation_type")

    difficulty = _parse_difficulty(lower)
    if difficulty is not None:
        slots.difficulty_preference = difficulty
        captured.add("difficulty_preference")

    for level in ("budget", "moderate", "comfort"):
        if re.search(rf"\b{level}\b", lower):
            slots.budget_level = level
            break

    return captured


def update_slots_from_tool_call(
    slots: PlanningSlots,
    tool_name: str,
    tool_input: dict,
) -> None:
    """Backfill slots from explicit tool inputs for determinism."""
    if tool_name == "get_route":
        start = tool_input.get("start")
        end = tool_input.get("end")
        if isinstance(start, str) and start.strip():
            slots.start = _normalize_location(start)
        if isinstance(end, str) and end.strip():
            slots.end = _normalize_location(end)
        distance = tool_input.get("daily_distance_km")
        if isinstance(distance, (int, float)):
            slots.daily_distance_km = float(distance)

    if tool_name == "get_weather":
        month = tool_input.get("month")
        if isinstance(month, int) and 1 <= month <= 12:
            slots.month = month

    if tool_name == "find_accommodation":
        acc_type = tool_input.get("accommodation_type")
        if isinstance(acc_type, str):
            try:
                slots.accommodation_type = AccommodationType(acc_type)
            except ValueError:
                pass

    if tool_name == "estimate_budget":
        level = tool_input.get("budget_level")
        if isinstance(level, str) and level.lower().strip() in {"budget", "moderate", "comfort"}:
            slots.budget_level = level.lower().strip()


def inject_slot_defaults_into_tool_input(tool_name: str, tool_input: dict, session) -> dict:
    """Fill missing tool inputs from parsed slots to keep tool use consistent with preferences."""
    effective_input = dict(tool_input)
    slots = session.planning_slots

    if tool_name == "get_route":
        if "daily_distance_km" not in effective_input and slots.daily_distance_km is not None:
            effective_input["daily_distance_km"] = slots.daily_distance_km

    if tool_name == "get_weather":
        if "month" not in effective_input and slots.month is not None:
            effective_input["month"] = slots.month

    if tool_name == "find_accommodation":
        if "accommodation_type" not in effective_input and slots.accommodation_type is not None:
            effective_input["accommodation_type"] = slots.accommodation_type.value

    if tool_name == "estimate_budget":
        if "accommodation_type" not in effective_input and slots.accommodation_type is not None:
            effective_input["accommodation_type"] = slots.accommodation_type.value
        if "budget_level" not in effective_input and slots.budget_level is not None:
            effective_input["budget_level"] = slots.budget_level

    return effective_input


def build_planning_constraints(session) -> str:
    """Build structured constraints from parsed slots for the model system prompt."""
    slots = session.planning_slots
    lines: list[str] = []

    if slots.start and slots.end:
        lines.append(f"- Route: {slots.start} to {slots.end}")

    if slots.month:
        timing = f"month {slots.month}"
        if slots.travel_timing_note:
            timing = slots.travel_timing_note
        approx = " (approximate)" if slots.travel_timing_is_approximate else ""
        lines.append(f"- Travel timing: {timing}{approx}")

    if slots.daily_distance_km is not None:
        lines.append(f"- Daily distance target: {slots.daily_distance_km:.0f} km/day")

    if slots.budget_per_day_eur is not None:
        lines.append(f"- Budget target: €{slots.budget_per_day_eur:.0f}/day")

    if slots.accommodation_type is not None:
        if (
            slots.accommodation_secondary_type is not None
            and slots.accommodation_secondary_every_n_nights is not None
            and slots.accommodation_secondary_type != slots.accommodation_type
        ):
            lines.append(
                "- Accommodation strategy: mostly "
                f"{slots.accommodation_type.value}, but "
                f"{slots.accommodation_secondary_type.value} every "
                f"{slots.accommodation_secondary_every_n_nights}th night"
            )
        else:
            lines.append(
                f"- Accommodation preference: {slots.accommodation_type.value}"
            )

    if slots.difficulty_preference is not None:
        lines.append(
            f"- Difficulty preference: {slots.difficulty_preference.value}"
        )

    if not lines:
        return ""

    return (
        "\\n\\n## Structured Planning Constraints (Server Parsed)\\n"
        + "\\n".join(lines)
        + "\\n- Follow these constraints unless the user explicitly changes them."
    )
