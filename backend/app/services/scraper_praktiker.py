"""
Minimal scraper for praktiker.bg search + product card parsing.

IMPORTANT: Always check robots.txt and the site's Terms of Service.
Add rate limiting and proper headers for production use.
"""
import httpx
from bs4 import BeautifulSoup
from typing import Optional

BASE = "https://praktiker.bg"
SEARCH = BASE + "/bg/search?query={query}"

HEADERS = {
    "User-Agent": "PriceCompareBot/1.0 (+contact@example.com)"
}


async def _fetch(url: str) -> str:
    async with httpx.AsyncClient(timeout=20) as client:
        r = await client.get(url, headers=HEADERS)
        r.raise_for_status()
        return r.text


async def search_by_barcode(barcode: str) -> Optional[dict]:
    """
    Try to find a product by barcode using the site's search.
    Returns dict with keys: sku, name, url, barcode, price (if parseable).
    """
    html = await _fetch(SEARCH.format(query=barcode))
    soup = BeautifulSoup(html, "html.parser")

    # These selectors are guesses; adjust to real DOM.
    card = soup.select_one(".product-card, .product, .catalog__product")
    if not card:
        return None

    name_el = card.select_one(".title a, .product-title a, a")
    url = name_el.get("href") if name_el else None
    if url and url.startswith("/"):
        url = BASE + url

    sku_el = card.select_one("[data-sku], .sku, .product-code")
    sku = (sku_el.get_text(strip=True) if sku_el else None) or barcode

    price_el = card.select_one(".price, .product-price__current")
    price_txt = price_el.get_text(strip=True).replace(",", ".") if price_el else None
    price = None
    if price_txt:
        # Keep only digits and dot
        num = "".join(ch for ch in price_txt if ch.isdigit() or ch == ".")
        try:
            price = float(num) if num else None
        except Exception:
            price = None

    name = name_el.get_text(strip=True) if name_el else ""

    return {"sku": sku, "name": name, "url": url, "barcode": barcode, "price": price}
