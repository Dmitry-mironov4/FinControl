from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router()


@router.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "📖 Справка FinControl\n"
        "─────────────────────\n"
        "Кнопки внизу:\n"
        "  ➕ Доход / ➖ Расход — добавить транзакцию\n"
        "  💰 Баланс — баланс и статистика за месяц\n"
        "  📋 История — все операции с фильтром\n"
        "  🎯 Цели / 📑 Подписки — цели и подписки\n"
        "  ⏰ Таймер — антиимпульсный таймер покупки\n"
        "  ⚙️ Настройки — время уведомлений\n\n"
        "Быстрое добавление:\n"
        "<code>+5000 Зарплата</code>          — доход\n"
        "<code>-300 Еда кофе в маке</code>    — расход с описанием\n"
        "<code>-1200 Транспорт, метро</code>  — запятая как разделитель\n\n"
        "Команды:\n"
        "/goals         — цели\n"
        "/subscriptions — подписки\n"
        "/timer         — таймер покупки\n"
        "/cancel        — отменить диалог\n"
        "/help          — эта справка"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Алиас: /stats → тот же UI, что и кнопка 💰 Баланс."""
    from bot.handlers.kb_buttons import kb_balance
    await kb_balance(message)
