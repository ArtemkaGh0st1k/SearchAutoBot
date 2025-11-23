# src/parsers/auto_ru.py

from src.parsers.base import BaseParser
from bs4 import BeautifulSoup

class AutoRuParser(BaseParser):
    async def parse(self, soup: BeautifulSoup) -> list:
        ads = []
        for a in soup.select("a.ListingItemTitle__link"):
            title = a.get_text(strip=True)
            link = a["href"]
            price_div = a.find_parent().select_one(".ListingItemPrice__content")
            price = price_div.get_text(strip=True) if price_div else "Цена не указана"
            ads.append({"title": title, "link": link, "price": price})
        return ads