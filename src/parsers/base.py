# src/parsers/base.py
# Абстрактный класс для парсеров (полиморфизм: переопределяй parse() для новых сайтов)

from abc import ABC, abstractmethod
from bs4 import BeautifulSoup
from src.config import Config

class BaseParser(ABC):
    def __init__(self, config: Config):
        self.log = config.log

    @abstractmethod
    async def parse(self, soup: BeautifulSoup) -> list:
        pass