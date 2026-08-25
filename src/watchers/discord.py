from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DiscordBoostPlan:
    months: int
    quantity: int = 14

    def total_from_unit_price(self, unit_price: float) -> float:
        return unit_price * self.quantity


BOOST_PLANS = (
    DiscordBoostPlan(months=1, quantity=14),
    DiscordBoostPlan(months=3, quantity=14),
)

NITRO_PLANS = (1, 12)
NITRO_BASIC_PLANS = (1, 12)


def calculate_boost_total(unit_price: float, quantity: int = 14) -> float:
    """Calculate a 14x Boost package from a per-Boost listing price."""
    return unit_price * quantity
