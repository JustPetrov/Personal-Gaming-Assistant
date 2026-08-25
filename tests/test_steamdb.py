from bs4 import BeautifulSoup

from src.watchers.steamdb import SteamDBClient


def test_currency_value_prefers_displayed_value():
    assert SteamDBClient._currency_value("Current Price €29.99 / €39.99", "€") == "€29.99"
    assert SteamDBClient._currency_value("Current Price ₴899 / ₴999", "₴") == "₴899"


def test_current_price_context_uses_labeled_section():
    html = """
    <html><body>
      <div>Historical €9.99</div>
      <div><span>Current Price</span><strong>€29.99</strong><strong>₴899</strong></div>
      <div>Historical €4.99</div>
    </body></html>
    """
    soup = BeautifulSoup(html, "html.parser")
    context = SteamDBClient._current_price_context(soup, soup.get_text(" ", strip=True))
    assert "€29.99" in context
    assert "₴899" in context
