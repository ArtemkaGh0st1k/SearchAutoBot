# src/parsers/avito.py
# Конкретный парсер (наследник)

from src.parsers.base import BaseParser
from bs4 import BeautifulSoup

class AvitoParser(BaseParser):
    async def parse(self, soup: BeautifulSoup) -> list:
        ads = []
        for item in soup.find_all("div", {"data-marker": "item"}):
            a = item.find("a", {"data-marker": "item-title"})

            if not a: continue

            title = a.get("title") or a.get_text(strip=True)
            link = "https://www.avito.ru" + a["href"]
            price = item.find("meta", {"itemprop": "price"})
            price = price["content"] + " ₽" if price else "Цена не указана"
            ads.append({"title": title, "link": link, "price": price})
            
        return ads