from __future__ import annotations

from datetime import datetime


def price_row(product: str, price: str | None, stock: str | None, url: str | None, source: str) -> str:
    return f"| {product} | {price or '—'} | {stock or '—'} | {f'[{source}]({url})' if url else '—'} | {source} |"


def section(title: str, rows: list[str]) -> str:
    header = [
        f"## {title}",
        "",
        "| Product | 💰 Actuele prijs | 📦 Stock | 🔗 Link | 📰 Bron |",
        "|---|---:|---|---|---|",
    ]
    return "\n".join(header + rows)


def late_night_roundup(changes: list[str], checked_at: datetime) -> str:
    lines = [
        "# 🌙 Late Night Round Up",
        "",
        f"**Laatste controle:** {checked_at.strftime('%Y-%m-%d %H:%M')}",
        "",
    ]
    if changes:
        lines.extend(f"- {change}" for change in changes)
    else:
        lines.append("Geen belangrijke wijzigingen sinds de vorige update.")
    return "\n".join(lines)
