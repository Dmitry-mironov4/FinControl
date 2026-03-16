import os
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# загружаем данные из .env файла
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# проверяем, что токен существует
if not BOT_TOKEN:
    raise ValueError("Токен в файле .env не найден")