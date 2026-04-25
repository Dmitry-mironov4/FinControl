"""Декоратор для обработчиков бота: ловит ошибки БД и прочие исключения.

Любой хендлер, который ходит в `fincontrolapp.db_queries`, может упасть
на уровне SQLite (блокировка, повреждение, отсутствие таблицы) или на
непредвиденном исключении в бизнес-логике. Без обёртки пользователь получит
молчаливый тайм-аут, а traceback уйдёт только в stderr.

Использование:

    @router.message(Command("stats"))
    @safe_db()
    async def cmd_stats(message: Message):
        ...

Порядок декораторов важен: `@safe_db()` должен стоять НИЖЕ роутерного
декоратора — чтобы роутер регистрировал уже обёрнутую функцию.
"""

import logging
import sqlite3
from functools import wraps

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import CallbackQuery, Message

logger = logging.getLogger(__name__)


def safe_db(fallback_message: str = "Не удалось получить данные, попробуйте позже"):
    """Ловит sqlite3.Error / Exception, логирует и отвечает пользователю.

    Первый позиционный аргумент хендлера должен быть Message или CallbackQuery:
    - Message → `message.answer(fallback_message)`
    - CallbackQuery → `callback.answer(fallback_message, show_alert=True)`
    """

    def decorator(handler):
        @wraps(handler)
        async def wrapper(event, *args, **kwargs):
            try:
                return await handler(event, *args, **kwargs)
            except sqlite3.Error:
                logger.exception("SQLite error in handler %s", handler.__name__)
                await _notify_user(event, fallback_message)
            except TelegramBadRequest as e:
                if "message is not modified" in str(e):
                    # Нормальный исход — содержимое не изменилось, тихо игнорируем.
                    # Для callback закрываем «часики», для message ничего не делаем.
                    if isinstance(event, CallbackQuery):
                        try:
                            await event.answer()
                        except Exception:
                            pass
                else:
                    # Реальная ошибка Telegram — логируем и сообщаем.
                    logger.exception("TelegramBadRequest in handler %s", handler.__name__)
                    await _notify_user(event, fallback_message)
            except Exception:
                logger.exception("Unexpected error in handler %s", handler.__name__)
                await _notify_user(event, fallback_message)

        return wrapper

    return decorator


async def _notify_user(event, text: str) -> None:
    """Безопасно уведомляем пользователя — сам notify не должен падать."""
    try:
        if isinstance(event, CallbackQuery):
            await event.answer(text, show_alert=True)
        elif isinstance(event, Message):
            await event.answer(text)
    except Exception:
        logger.exception("Failed to notify user about error")
