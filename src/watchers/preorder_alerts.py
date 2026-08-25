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


def upcoming_bonus_alerts(items: list[PreorderItem], *, days_before: int = 21, now: datetime | None = None) -> list[dict]:
    """Return pre-order bonus alerts from 21 days before release/bonus cutoff."""
    now = now or datetime.now(timezone.utc)
    cutoff = now + timedelta(days=days_before)
    alerts: list[dict] = []
    for item in items:
        release = item.release_at
        if release.tzinfo is None:
            release = release.replace(tzinfo=timezone.utc)
        if now <= release <= cutoff and item.bonus:
            alerts.append({
                "type": "preorder_bonus_alert",
                "id": item.item_id,
                "title": item.title,
                "release_at": release.isoformat(),
                "days_remaining": max(0, (release - now).days),
                "bonus": item.bonus,
                "url": item.url,
                "warning_window_days": days_before,
            })
    return alerts
