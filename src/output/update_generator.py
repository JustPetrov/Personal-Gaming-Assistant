from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from watchers.change_detection import ChangeType, ObservationChange


@dataclass(frozen=True)
class UpdateContext:
    title: str
    local_location: str
    local_time: str
    local_date: str
    nl_time: str
    nl_date: str


def _change_line(change: ObservationChange) -> str:
    current = change.current or change.previous
    assert current is not None
    name = current.product
    if change.change_type is ChangeType.NEW:
        return f"- 🆕 **{name}** — nieuw"
    if change.change_type is ChangeType.PRICE_CHANGED:
        old = change.previous.price if change.previous else "—"
        new = change.current.price if change.current else "—"
        return f"- 💰 **{name}** — {old} → **{new}**"
    if change.change_type is ChangeType.STOCK_CHANGED:
        old = change.previous.stock if change.previous else "—"
        new = change.current.stock if change.current else "—"
        return f"- 📦 **{name}** — stock: {old} → **{new}**"
    if change.change_type is ChangeType.LINK_CHANGED:
        return f"- 🔗 **{name}** — link gewijzigd"
    if change.change_type is ChangeType.SOURCE_CHANGED:
        return f"- 📰 **{name}** — bron gewijzigd"
    if change.change_type is ChangeType.REMOVED:
        return f"- ❌ **{name}** — verdwenen uit de huidige bron"
    return ""


def render_update(context: UpdateContext, changes: Iterable[ObservationChange]) -> str:
    lines = [
        f"# 🎮 {context.title}",
        "",
        "## ℹ️ Informatie",
        "",
        "| | |",
        "|---|---|",
        f"| 📍 **Lokale locatie** | {context.local_location} |",
        f"| 🕐 **Lokale tijd** | {context.local_time} |",
        f"| 📅 **Lokale datum** | {context.local_date} |",
        f"| 🇳🇱 **Nederlandse tijd** | {context.nl_time} |",
        f"| 📅 **Nederlandse datum** | {context.nl_date} |",
        "",
        "## 🔄 Wijzigingen",
        "",
    ]
    change_lines = [_change_line(change) for change in changes]
    change_lines = [line for line in change_lines if line]
    lines.extend(change_lines or ["Geen relevante wijzigingen sinds de vorige controle."])
    return "\n".join(lines)


def render_late_night_round_up(context: UpdateContext, changes: Iterable[ObservationChange]) -> str:
    """Compact 22:00 summary intended to accompany the normal update."""
    lines = ["## 🌙 Late Night Round Up", ""]
    change_lines = [_change_line(change) for change in changes]
    change_lines = [line for line in change_lines if line]
    lines.extend(change_lines or ["Geen relevante wijzigingen sinds de 20:00-update."])
    return "\n".join(lines)
