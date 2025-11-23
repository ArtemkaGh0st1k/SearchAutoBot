# src/bot_commands.py
# Класс для обработчиков команд (расширяемо: добавляй новые методы, напр., def filter_price())

from telegram import Update
from telegram.ext import ContextTypes
from src.databases.database import DatabaseManager
from src.config import Config

class BotCommands:
    def __init__(self, config: Config, db_manager: DatabaseManager):
        self.config = config
        self.db_manager = db_manager
        self.log = config.log

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_html(
            "Привет! Я бот-поисковик авто\n\n"
            "Просто напиши в любом чате:\n"
            "<code>/add BMW M5 F90</code> — и я буду присылать новые объявления <b>именно сюда</b>\n\n"
            "Команды:\n"
            "/add <модель> — добавить в этот чат\n"
            "/remove <модель> — убрать из этого чата\n"
            "/mylist — что я ищу в этом чате\n"
            "/mychats — все твои подписки\n"
            "/help — эта справка"
        )

    async def add(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("Пример: /add Porsche 911 Turbo S")
            return

        query = " ".join(context.args).strip()
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id

        await self.db_manager.add_subscription(user_id, chat_id, query)
        await update.message.reply_text(f"Теперь я присылаю «{query.upper()}» именно в этот чат")

    async def remove(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("Пример: /remove BMW M5")
            return

        query = " ".join(context.args).strip()
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id

        rowcount = await self.db_manager.remove_subscription(user_id, chat_id, query)
        if rowcount == 0:
            await update.message.reply_text("Такой подписки в этом чате не было")
        else:
            await update.message.reply_text(f"Больше не буду присылать «{query.upper()}» сюда")

    async def mylist(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id

        queries = await self.db_manager.get_chat_subscriptions(user_id, chat_id)
        if not queries:
            await update.message.reply_text("В этом чате ты ничего не ищешь\nНапиши /add <модель>")
            return

        models = "\n".join([f"• {q.upper()}" for q in queries])
        await update.message.reply_text(f"В этом чате ты ищешь:\n{models}")

    async def mychats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        subscriptions = await self.db_manager.get_all_user_subscriptions(user_id)
        if not subscriptions:
            await update.message.reply_text("У тебя пока нет подписок")
            return

        text = "Твои подписки по чатам:\n\n"
        current_chat_id = None
        for chat_id, query in subscriptions:
            if chat_id != current_chat_id:
                try:
                    chat = await context.bot.get_chat(chat_id)
                    title = chat.title or ("Личный чат" if chat.type == "private" else "Группа/канал")
                except Exception as e:
                    self.log.warning(f"Не удалось получить чат {chat_id}: {e}")
                    title = f"Чат ID {chat_id}"
                text += f"{title}\n"
                current_chat_id = chat_id
            text += f"   • {query.upper()}\n"

        await update.message.reply_text(text)

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.start(update, context)  # Алиас