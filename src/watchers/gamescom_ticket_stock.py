from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class TicketStock(StrEnum):
    AVAILABLE = "available"
    LOW = "low"
    EVENING_ONLY = "evening_only"
    SOLD_OUT = "sold_out"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class TicketStatus:
    day: str
    stock: TicketStock
    regular_available: bool
    evening_available: bool
    url: str | None = None


def classify_ticket_status(
    *,
    regular_available: bool,
    evening_available: bool,
    low_stock: bool = False,
) -> TicketStock:
    if not regular_available and not evening_available:
        return TicketStock.SOLD_OUT
    if not regular_available and evening_available:
        return TicketStock.EVENING_ONLY
    if low_stock:
        return TicketStock.LOW
    return TicketStock.AVAILABLE


def stock_alert(status: TicketStatus) -> str | None:
    if status.stock is TicketStock.SOLD_OUT:
        return f"🎟️ {status.day}: uitverkocht"
    if status.stock is TicketStock.EVENING_ONLY:
        return f"⚠️ {status.day}: alleen Evening Tickets (vanaf 16:00) beschikbaar"
    if status.stock is TicketStock.LOW:
        return f"⚠️ {status.day}: lage ticketvoorraad"
    return None
