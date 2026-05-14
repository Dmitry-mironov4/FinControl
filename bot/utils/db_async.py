"""Обёртка для вызова синхронных функций БД из async-хендлеров.

`fincontrolapp.db_queries` — синхронный модуль (sqlite3). Прямой вызов
из async-хендлера блокирует event loop aiogram: пока SQLite обрабатывает
запрос, бот не может обслуживать других пользователей.

`run_db` уводит вызов в пул потоков через `asyncio.to_thread`, чтобы
event loop оставался отзывчивым.

Использование:

    from bot.utils.db_async import run_db
    from fincontrolapp.db_queries import get_balance

    balance = await run_db(get_balance, user["id"])
"""

from asyncio import to_thread


async def run_db(func, *args, **kwargs):
    return await to_thread(func, *args, **kwargs)
