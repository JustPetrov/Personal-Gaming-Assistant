from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class PreorderItem:
    item_id: str
    title: str
    release_at: datetime
    bonus: str | None
    url: str | None
    bonus_deadline: datetime | None = None
    active: bool = True


def upcoming_bonus_alerts(
    items: list[PreorderItem],
    *,
    days_before: int = 21,
    now: datetime | None = None,
) -> list[dict]:
    """Return active pre-order bonus alerts from 21 days before the bonus deadline.

    The bonus deadline is authoritative when supplied. Release time is used only
    as a backwards-compatible fallback for legacy entries that do not yet store
    a dedicated deadline.
    """
    now = now or datetime.now(timezone.utc)
    cutoff = now + timedelta(days=days_before)
    alerts: list[dict] = []

    for item in items:
        if not item.active or not item.bonus:
            continue

        deadline = item.bonus_deadline or item.release_at
        if deadline.tzinfo is None:
            deadline = deadline.replace(tzinfo=timezone.utc)

        if deadline < now:
            continue

        if now <= deadline <= cutoff or now > deadline - timedelta(days=days_before):
            alerts.append(
                {
                    "type": "preorder_bonus_alert",
                    "id": item.item_id,
                    "title": item.title,
                    "release_at": _aware(item.release_at).isoformat(),
                    "bonus_deadline": deadline.isoformat(),
                    "days_remaining": max(0, (deadline - now).days),
                    "bonus": item.bonus,
                    "url": item.url,
                    "active": item.active,
                    "warning_window_days": days_before,
                }
            )

    return alerts


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
