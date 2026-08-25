from __future__ import annotations

NEWS_SECTIONS = (
    ("GamesCom", ("Countdown", "Beschikbare Tickets", "Nieuwe EPIX Quests", "GamesCom Nieuws", "GamesCom Travel List")),
    ("Game Nieuws", ("Hardware", "Games", "ETS 2/ATS")),
    ("Hardware Price Watcher", ("Opgeslagen Hardware prijzen",)),
    ("Game Price Watcher", ("Opgeslagen game prijzen", "Aflopende Pre-order bonussen")),
    ("UAH Deals", ("Beste koop route",)),
    ("Discord Price Watcher", ("Huidige G2G Prijzen (Nitro & Server Boosts)",)),
    ("RAM Watcher", ("Rammegedon actief?", "Gemiddelde marktprijs (32GB, 48GB, 64GB & 96GB DDR5)")),
    ("GPU Watcher", ("GPU Doomsday actief?", "Gemiddelde marktprijs per GPU-range")),
    ("Aanbevelingen", ("Deals", "Game Aanbevelingen (PS5 en Steam)")),
    ("Round-Up", ("Korte samenvatting van dit nieuwsbericht",)),
)

HEADER_FIELDS = ("Lokale Datum + Tijd", "Nederlandse Datum + Tijd", "Update type")


def build_news_prompt(context: str, update_type: str, local_datetime: str, nl_datetime: str) -> str:
    sections = "\n".join(f"- {title}: {', '.join(items)}" for title, items in NEWS_SECTIONS)
    return f"""Schrijf een Nederlandse gaming-update volgens exact deze structuur.

Titel
- {local_datetime}, {nl_datetime}, {update_type}

{sections}

Regels:
- Gebruik alleen feiten uit CONTEXT; verzin niets.
- Toon een sectie alleen wanneer er relevante gegevens zijn.
- UAH Deals alleen tonen wanneer Game Price Watcher daadwerkelijk games met Steam/UAH-data bevat.
- Pre-order bonussen minimaal 3 weken vooraf signaleren wanneer de bron dat ondersteunt.
- RAM/GPU status alleen actief noemen wanneer de ingestelde 14-dagen-instabiliteitsregel door data wordt ondersteund.
- GamesCom Travel List is een aparte toekomstige bron/sectie en mag leeg blijven tot die wordt geconfigureerd.
- Round-Up is altijd kort.
- Dit is de 22:00-update alleen als UPDATE TYPE expliciet 'Late Night Update' is; dan is Round-Up een uitgebreidere Late Night Round-Up over de hele dag.

CONTEXT:
{context}
"""
