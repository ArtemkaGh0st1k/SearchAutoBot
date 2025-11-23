# src/monitoring.py
# Класс для мониторинга (расширяемо: добавь threading для parallelism или celery для дистрибуции)

import asyncio
import aiohttp
import hashlib
from bs4 import BeautifulSoup
from telegram.ext import Application
from src.config.config import Config
from src.databases.database import DatabaseManager
from src.parsers.base import BaseParser

class MonitoringService:
    def __init__(self, config: Config, db_manager: DatabaseManager, app: Application):
        self.config = config
        self.db_manager = db_manager
        self.app = app
        self.log = config.log
        self.parsers = {}  # Кэш парсеров: { 'AvitoParser': instance }

    def _get_parser(self, parser_class_name: str) -> BaseParser:
        if parser_class_name not in self.parsers:
            # Динамическая загрузка класса парсера (расширяемо)
            module_name = parser_class_name.lower().replace('parser', '')
            module = __import__(f"src.parsers.{module_name}", fromlist=[parser_class_name])
            parser_class = getattr(module, parser_class_name)
            self.parsers[parser_class_name] = parser_class(self.config)
        return self.parsers[parser_class_name]

    async def _check_site(self, session, site, query):
        try:
            async with session.get(site["url"], params=site["params"](query), timeout=20) as resp:
                if resp.status != 200:
                    return []
                html = await resp.text()
                soup = BeautifulSoup(html, "html.parser")
                parser = self._get_parser(site["parser_class"])
                return await parser.parse(soup)
        except Exception as e:
            self.log.error(f"Ошибка парсинга {site['name']} для '{query}': {e}")
        return []

    async def run_loop(self):
        await asyncio.sleep(10)  # Ждём запуска бота
        seen = await self.db_manager.load_seen_ads()
        self.log.info("Мониторинг запущен")

        while True:
            try:
                subscriptions = await self.db_manager.get_all_subscriptions()
                if not subscriptions:
                    await asyncio.sleep(60)
                    continue

                async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=30)) as session:
                    for chat_id, query in subscriptions:
                        query_clean = query.strip()
                        for site in self.config.sites:
                            ads = await self._check_site(session, site, query_clean)
                            for ad in ads:
                                h = hashlib.md5(ad["link"].encode()).hexdigest()
                                if h not in seen:
                                    seen.add(h)
                                    await self.db_manager.add_seen_ad(h)

                                    msg = (
                                        f"*Найдено: {query_clean.upper()}*\n\n"
                                        f"{ad['title']}\n"
                                        f"{ad['price']}\n\n"
                                        f"{ad['link']}"
                                    )
                                    try:
                                        await self.app.bot.send_message(
                                            chat_id=chat_id,
                                            text=msg,
                                            parse_mode='Markdown',
                                            disable_web_page_preview=False
                                        )
                                    except Exception as e:
                                        self.log.warning(f"Ошибка отправки в {chat_id}: {e}")
                            await asyncio.sleep(0.5)  # Антифлуд
            except Exception as e:
                self.log.error(f"Ошибка в мониторинге: {e}")

            await asyncio.sleep(self.config.check_interval)