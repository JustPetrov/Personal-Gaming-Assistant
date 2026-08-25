from __future__ import annotations


def filter_ticket_alerts(statuses: list[dict], selections: list[dict]) -> list[dict]:
    """Keep GamesCom stock alerts relevant to selected visit days/ticket types."""
    wanted = {(str(item.get("day")), str(item.get("ticket_type", "regular"))) for item in selections}
    result: list[dict] = []
    for status in statuses:
        day = str(status.get("day"))
        regular = (day, "regular")
        evening = (day, "evening")
        if regular in wanted and status.get("regular_available") is not None:
            result.append({**status, "ticket_type": "regular"})
        if evening in wanted and status.get("evening_available") is not None:
            result.append({**status, "ticket_type": "evening"})
    return result
