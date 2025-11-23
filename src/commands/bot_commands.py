from turtle import update
import aiosqlite
from telegram import Update
from telegram import BotCommand 
from telegram.ext import ContextTypes
from src.databases.database import DatabaseManager
from src.config.config import Config

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
            "/add &lt;модель&gt; — добавить в этот чат\n"
            "/remove &lt;модель&gt; — убрать из этого чата\n"
            "/mylist — что я ищу в этом чате\n"
            "/mychats — все твои подписки\n"
            "/help — эта справка"
        )

    async def set_bot_commands(self, bot):
        commands = [
            BotCommand("start", "Запустить бота и показать справку"),
            BotCommand("add", "Добавить модель в этот чат (пример: /add BMW M5)"),
            BotCommand("remove", "Убрать модель из этого чата (пример: /remove BMW M5)"),
            BotCommand("pause", "Приостановить уведомления по модели (пример: /pause BMW M5)"),
            BotCommand("resume", "Возобновить уведомления по модели (пример: /resume BMW M5)"),
            BotCommand("clear_chat", "Очистить все подписки в этом чате"),
            BotCommand("mylist", "Список моделей в этом чате"),
            BotCommand("mychats", "Все твои подписки по чатам"),
            BotCommand("help", "Показать справку"),
        ]
        await bot.set_my_commands(commands)
        self.log.info("Меню команд установлено")


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

        queries = await self.db_manager.get_chat_subscriptions(user_id, chat_id)  # Обновите get_chat_subscriptions, если нужно фильтр

        if not queries:
            await update.message.reply_text("В этом чате ты ничего не ищешь\nНапиши /add &lt;модель&gt;")
            return

        models = "\n".join([f"• {q[0].upper()} ({'активно' if q[1] else 'приостановлено'})" for q in queries])
        await update.message.reply_text(f"В этом чате ты ищешь:\n{models}")


    async def mychats(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        subscriptions = await self.db_manager.get_all_user_subscriptions(user_id)
        if not subscriptions:
            await update.message.reply_text("У тебя пока нет подписок")
            return

        text = "Твои подписки по чатам:\n\n"
        current_chat_id = None
        for chat_id, query, is_active in subscriptions:
            status = 'активно' if is_active else 'приостановлено'
            if chat_id != current_chat_id:
                try:
                    chat = await context.bot.get_chat(chat_id)
                    title = chat.title or ("Личный чат" if chat.type == "private" else "Группа/канал")
                except Exception as e:
                    self.log.warning(f"Не удалось получить чат {chat_id}: {e}")
                    title = f"Чат ID {chat_id}"
                text += f"{title}\n"
                current_chat_id = chat_id
            text += f"   • {query.upper()} ({status})\n"

        await update.message.reply_text(text)


    async def clear_chat(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id

        async with aiosqlite.connect(self.db_manager.db_file) as db:
            cursor = await db.execute(
                "DELETE FROM subscriptions WHERE user_id = ? AND chat_id = ?",
                (user_id, chat_id)
            )
            await db.commit()

        if cursor.rowcount == 0:
            await update.message.reply_text("В этом чате у тебя ничего не было")
        else:
            await update.message.reply_text(f"Очистил все подписки в этом чате ({cursor.rowcount} удалено)")


    async def pause(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("Пример: /pause BMW M5")
            return

        query = " ".join(context.args).strip().lower()
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id

        async with aiosqlite.connect(self.db_manager.db_file) as db:
            cursor = await db.execute(
                "UPDATE subscriptions SET is_active = 0 WHERE user_id = ? AND chat_id = ? AND query = ?",
                (user_id, chat_id, query)
            )
            await db.commit()

        if cursor.rowcount == 0:
            await update.message.reply_text("Такой модели в этом чате не было")
        else:
            await update.message.reply_text(f"Приостановил уведомления для «{query.upper()}» в этом чате")


    async def resume(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("Пример: /resume BMW M5")
            return

        query = " ".join(context.args).strip().lower()
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id

        async with aiosqlite.connect(self.db_manager.db_file) as db:
            cursor = await db.execute(
                "UPDATE subscriptions SET is_active = 1 WHERE user_id = ? AND chat_id = ? AND query = ?",
                (user_id, chat_id, query)
            )
            await db.commit()

        if cursor.rowcount == 0:
            await update.message.reply_text("Такой модели в этом чате не было")
        else:
            await update.message.reply_text(f"Возобновил уведомления для «{query.upper()}» в этом чате")

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.start(update, context)  # Алиас