# src/parsers/drom.py

from src.parsers.base import BaseParser
from bs4 import BeautifulSoup

class DromParser(BaseParser):
    async def parse(self, soup: BeautifulSoup) -> list:
        ads = []
        for a in soup.find_all("a", {"data-ftid": "bulls-list_bull"}):
            span = a.find("span")

            if not span: continue

            title = span.get_text(strip=True)
            link = a["href"]
            price_span = a.find("span", {"data-ftid": "bull_price"})
            price = price_span.get_text(strip=True) if price_span else "Цена не указана"
            ads.append({"title": title, "link": link, "price": price})
            
        return ads