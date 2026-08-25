from __future__ import annotations

from unittest.mock import patch

from watchers.gamescom_ticket_live import GamesComTicketLiveClient
from watchers.gamescom_ticket_stock import TicketStatus, TicketStock
from watchers.watcher_registry_gamescom import _ticket_stock_fetcher


def test_ticket_stock_fetcher_exposes_day_status():
    statuses = [
        TicketStatus(
            day="Friday",
            stock=TicketStock.AVAILABLE,
            regular_available=True,
            evening_available=True,
            url="https://tickets.gamescom.global/",
        )
    ]
    with patch.object(GamesComTicketLiveClient, "fetch_statuses", return_value=statuses):
        rows = list(_ticket_stock_fetcher())

    assert rows[0]["type"] == "gamescom_ticket_status"
    assert rows[0]["day"] == "Friday"
    assert rows[0]["stock"] == TicketStock.AVAILABLE.value
    assert rows[0]["regular_available"] is True
    assert rows[0]["evening_available"] is True
