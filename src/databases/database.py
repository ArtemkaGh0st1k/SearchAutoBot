# src/database.py
# Класс для управления БД (расширяемо: добавь миграции, asyncpg для Postgres)

import aiosqlite
from src.config.config import Config

class DatabaseManager:
    def __init__(self, config: Config):
        self.db_file = config.db_file
        self.log = config.log

    async def initialize(self):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    chat_id INTEGER,
                    query TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, chat_id, query)
                )
            ''')
            await db.commit()
        self.log.info("База данных инициализирована")

    async def add_subscription(self, user_id: int, chat_id: int, query: str):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute(
                "INSERT OR REPLACE INTO subscriptions (user_id, chat_id, query) VALUES (?, ?, ?)",
                (user_id, chat_id, query.lower())
            )
            await db.commit()

    async def remove_subscription(self, user_id: int, chat_id: int, query: str) -> int:
        async with aiosqlite.connect(self.db_file) as db:
            cursor = await db.execute(
                "DELETE FROM subscriptions WHERE user_id = ? AND chat_id = ? AND query = ?",
                (user_id, chat_id, query.lower())
            )
            await db.commit()
            return cursor.rowcount

    async def get_chat_subscriptions(self, user_id: int, chat_id: int) -> list:
        async with aiosqlite.connect(self.db_file) as db:
            async with db.execute(
                "SELECT query, is_active FROM subscriptions WHERE user_id = ? AND chat_id = ? ORDER BY query",
                (user_id, chat_id)
            ) as cursor:
                return await cursor.fetchall()  # Теперь возвращает [(query, is_active), ...]

async def get_all_user_subscriptions(self, user_id: int) -> list:
    async with aiosqlite.connect(self.db_file) as db:
        async with db.execute(
            "SELECT chat_id, query, is_active FROM subscriptions WHERE user_id = ? ORDER BY chat_id, query",
            (user_id,)
        ) as cursor:
            return await cursor.fetchall()  # [(chat_id, query, is_active), ...]

    async def get_all_subscriptions(self) -> list:
        async with aiosqlite.connect(self.db_file) as db:
            async with db.execute("SELECT chat_id, query FROM subscriptions WHERE is_active = 1") as cursor:
                return await cursor.fetchall()

    async def load_seen_ads(self) -> set:
        seen = set()
        async with aiosqlite.connect(self.db_file) as db:
            async with db.execute("SELECT hash FROM seen_ads") as cursor:
                async for row in cursor:
                    seen.add(row[0])
        return seen

    async def add_seen_ad(self, ad_hash: str):
        async with aiosqlite.connect(self.db_file) as db:
            await db.execute("INSERT OR IGNORE INTO seen_ads (hash) VALUES (?)", (ad_hash,))
            await db.commit()