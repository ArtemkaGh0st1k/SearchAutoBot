# src/main.py
# Точка входа: создаёт объекты классов и запускает (композиция)

import asyncio
from telegram.ext import Application, CommandHandler
from src.databases.database import DatabaseManager
from src.commands.bot_commands import BotCommands
from src.services.monitoring import MonitoringService
from src.config.config import Config

async def main():
    config = Config()
    db_manager = DatabaseManager(config)
    await db_manager.initialize()

    app = Application.builder().token(config.token).build()

    bot_commands = BotCommands(config, db_manager)

    # Регистрация команд (расширяемо: добавляй новые CommandHandler)
    app.add_handler(CommandHandler("start", bot_commands.start))
    app.add_handler(CommandHandler("add", bot_commands.add))
    app.add_handler(CommandHandler("remove", bot_commands.remove))
    app.add_handler(CommandHandler("mylist", bot_commands.mylist))
    app.add_handler(CommandHandler("mychats", bot_commands.mychats))
    app.add_handler(CommandHandler("clear_chat", bot_commands.clear_chat))
    app.add_handler(CommandHandler("pause", bot_commands.pause))
    app.add_handler(CommandHandler("resume", bot_commands.resume))
    app.add_handler(CommandHandler("help", bot_commands.help))

    await bot_commands.set_bot_commands(app.bot)

    # Мониторинг как сервис
    monitoring_service = MonitoringService(config, db_manager, app)
    app.job_queue.run_once(lambda ctx: asyncio.create_task(monitoring_service.run_loop()), 1)

    config.log.info("Бот запускается...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)

    await asyncio.Event().wait()  # Держим живым

if __name__ == "__main__":
    asyncio.run(main())