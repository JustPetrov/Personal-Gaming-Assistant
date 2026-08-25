from __future__ import annotations

from dataclasses import dataclass

from gamescom.stock_status import StockStatus, normalize_stock_status


@dataclass(frozen=True)
class StockAlert:
    day: str
    ticket_type: str
    status: StockStatus
    message: str


def build_stock_alerts(statuses: list[dict]) -> list[StockAlert]:
    """Create alerts only for actionable stock changes; caller deduplicates state."""
    alerts: list[StockAlert] = []
    for item in statuses:
        day = str(item.get("day", ""))
        status = normalize_stock_status(
            regular_available=item.get("regular_available"),
            evening_available=item.get("evening_available"),
            low_stock=bool(item.get("low_stock", False)),
        )
        if status is StockStatus.AVAILABLE:
            continue
        ticket_type = "evening" if status is StockStatus.EVENING_ONLY else "regular"
        messages = {
            StockStatus.LOW: f"{day}: lage ticketvoorraad ({ticket_type})",
            StockStatus.EVENING_ONLY: f"{day}: alleen Evening Tickets zijn nog beschikbaar",
            StockStatus.SOLD_OUT: f"{day}: tickets zijn uitverkocht",
            StockStatus.UNKNOWN: f"{day}: ticketvoorraad onbekend",
        }
        alerts.append(StockAlert(day, ticket_type, status, messages[status]))
    return alerts
