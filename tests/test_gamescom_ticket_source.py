from src.watchers.gamescom_ticket_source import GamesComTicketSource


def test_classify_sold_out():
    regular, evening, low, sold_out = GamesComTicketSource.classify_text("Saturday: sold out")
    assert sold_out is True


def test_classify_evening_ticket():
    regular, evening, low, sold_out = GamesComTicketSource.classify_text("Evening Ticket from 16:00")
    assert evening is True


def test_classify_low_stock():
    regular, evening, low, sold_out = GamesComTicketSource.classify_text("Limited availability")
    assert low is True


def test_unknown_portal_is_not_sold_out():
    regular, evening, low, sold_out = GamesComTicketSource.classify_text("Gamescom visitor ticket portal")
    assert (regular, evening, low, sold_out) == (False, False, False, False)
