from __future__ import annotations

from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class VisitOption:
    day: str
    date: date
    regular_available: bool = True
    evening_available: bool = False


VISIT_DAYS = ("Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
EVENING_DAYS = frozenset({"Thursday", "Friday", "Saturday", "Sunday"})


def build_visit_options(dates: dict[str, date]) -> tuple[VisitOption, ...]:
    """Build selectable GamesCom visit options for the configured event dates."""
    options: list[VisitOption] = []
    for day in VISIT_DAYS:
        if day not in dates:
            continue
        options.append(VisitOption(day, dates[day], True, day in EVENING_DAYS))
    return tuple(options)


def normalize_selection(day: str, *, evening: bool = False) -> dict[str, object]:
    """Normalize dashboard selection; evening tickets are only valid Thu-Sun."""
    if day not in VISIT_DAYS:
        raise ValueError(f"Unsupported GamesCom visit day: {day}")
    if evening and day not in EVENING_DAYS:
        raise ValueError("Evening tickets are only available Thursday through Sunday")
    return {"day": day, "ticket_type": "evening" if evening else "regular"}
