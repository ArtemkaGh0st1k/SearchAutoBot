# src/config.py
# Класс для конфигурации (расширяемо: добавь методы load_from_yaml() и т.д.)

import os
import logging

class Config:
    def __init__(self):
        self.db_file = "carbot.db"
        self.check_interval = 300  # 5 минут
        self.token = os.getenv('SEARCHAUTOTESTBOT_TOKEN')

        if not self.token:
            raise ValueError("TOKEN не задан в environment variables!")

        # Сайты (список словарей для динамической загрузки парсеров)
        self.sites = \
        [
            {
                "name": "avito",
                "url": "https://www.avito.ru/all/avtomobili",
                "params": lambda q: {"q": q, "radius": 0},
                "parser_class": "AvitoParser"
            },
            {
                "name": "auto.ru",
                "url": "https://auto.ru/cars/used/",
                "params": lambda q: {"query": q},
                "parser_class": "AutoRuParser"
            },
            {
                "name": "drom",
                "url": "https://auto.drom.ru/",
                "params": lambda q: {"q": q},
                "parser_class": "DromParser"
            },
        ]

        # Логгинг (можно расширить: добавить file_handler)
        logging.basicConfig\
        (
            level=logging.INFO,
            format='%(asctime)s | %(levelname)s | %(message)s',
            handlers=[logging.StreamHandler()]
        )
        self.log = logging.getLogger(__name__)