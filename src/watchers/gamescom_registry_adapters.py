from __future__ import annotations

from collections.abc import Callable, Iterable

from .price_models import PriceObservation
from .epix_quests import EpixQuestClient, EpixQuestState


def epix_quest_fetcher() -> Iterable[PriceObservation]:
    """Expose newly discovered EPIX quests to the common watcher pipeline."""
    client = EpixQuestClient()
    try:
        state = EpixQuestState()
        new_quests = state.new_quests(client.fetch())
        for quest in new_quests:
            yield PriceObservation(
                product=f"EPIX Quest: {quest.title}",
                platform="gamescom EPIX",
                edition=None,
                price=None,
                currency=None,
                stock="New",
                url=quest.url,
                source="gamescom EPIX",
                checked_at=None,
            )
    finally:
        client.close()
