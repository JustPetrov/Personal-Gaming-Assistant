from src.watchers.gamescom_ticket_stock import TicketStock, classify_ticket_status, stock_alert, TicketStatus


def test_evening_only_is_distinct_from_sold_out():
    assert classify_ticket_status(regular_available=False, evening_available=True) is TicketStock.EVENING_ONLY
    assert classify_ticket_status(regular_available=False, evening_available=False) is TicketStock.SOLD_OUT


def test_low_stock_alert():
    status = TicketStatus("Sunday", TicketStock.LOW, True, True)
    assert "lage ticketvoorraad" in stock_alert(status)


def test_evening_only_alert_mentions_16():
    status = TicketStatus("Sunday", TicketStock.EVENING_ONLY, False, True)
    assert "16:00" in stock_alert(status)


def test_available_has_no_alert():
    status = TicketStatus("Friday", TicketStock.AVAILABLE, True, True)
    assert stock_alert(status) is None
