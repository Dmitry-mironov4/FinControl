import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from handlers import start, menu, quick_add, stats, add_dialog, subscriptions, goals, transactions
from handlers.notify import setup_notify_scheduler

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("Нет токена! Добавь BOT_TOKEN в .env файл")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

dp.include_router(start.router)
dp.include_router(add_dialog.router)
dp.include_router(goals.router)
dp.include_router(quick_add.router)  # must be before transactions.router to intercept cancel_tx
dp.include_router(transactions.router)
dp.include_router(stats.router)
dp.include_router(subscriptions.router)
dp.include_router(menu.router)

async def main():
    scheduler = setup_notify_scheduler(bot)
    scheduler.start()
    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()

if __name__ == "__main__":
    asyncio.run(main())