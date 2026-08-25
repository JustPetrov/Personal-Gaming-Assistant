from __future__ import annotations

from enum import StrEnum


class StockStatus(StrEnum):
    AVAILABLE = "available"
    LOW = "low"
    EVENING_ONLY = "evening_only"
    SOLD_OUT = "sold_out"
    UNKNOWN = "unknown"


def normalize_stock_status(*, regular_available: bool | None, evening_available: bool | None, low_stock: bool = False) -> StockStatus:
    """Normalize raw GamesCom ticket data into alert-friendly states."""
    if regular_available is False and evening_available is False:
        return StockStatus.SOLD_OUT
    if regular_available is False and evening_available is True:
        return StockStatus.EVENING_ONLY
    if regular_available is True and low_stock:
        return StockStatus.LOW
    if regular_available is True:
        return StockStatus.AVAILABLE
    return StockStatus.UNKNOWN
