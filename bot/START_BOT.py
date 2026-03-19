import os
import sys
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("Нет токена! Добавь BOT_TOKEN в .env файл")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

from handlers import start

dp.include_router(start.router)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())