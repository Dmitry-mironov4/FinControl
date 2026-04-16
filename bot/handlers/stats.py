import datetime
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from fincontrolapp.db_queries import get_user_by_telegram_id, get_balance, get_monthly_stats
from bot.utils.formatters import format_balance, fmt_amount

router = Router()

MONTH_NAMES = [
    "", "январь", "февраль", "март", "апрель", "май", "июнь",
    "июль", "август", "сентябрь", "октябрь", "ноябрь", "декабрь"
]

CATEGORY_EMOJIS = {
    "Еда": "🍕", "Продукты": "🛒", "Транспорт": "🚗", "Кафе": "☕",
    "Развлечения": "🎮", "Здоровье": "💊", "Одежда": "👕", "Покупки": "🛒",
    "Связь": "📱", "Коммуналка": "🏠", "Спорт": "🏋️", "Другое": "📦",
}


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    user = get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала запустите /start")
        return

    today = datetime.date.today()
    stats = get_monthly_stats(user["id"], today.year, today.month)
    month_name = MONTH_NAMES[today.month].capitalize()

    income = stats["income"]
    expenses = stats["expenses"]
    balance = income - expenses
    savings_rate = (balance / income * 100) if income > 0 else 0.0

    lines = [
        f"📊 Статистика за {month_name}:",
        "",
        f"💰 Баланс: {fmt_amount(balance)}₽",
        f"📈 Доходы: {fmt_amount(income)}₽",
        f"📉 Расходы: {fmt_amount(expenses)}₽",
        f"💾 Норма сбережений: {savings_rate:.1f}%",
    ]

    if stats["top_categories"] and expenses > 0:
        lines.append("")
        lines.append("Топ расходов:")
        for cat in stats["top_categories"]:
            emoji = CATEGORY_EMOJIS.get(cat["name"], "📦")
            pct = cat["total"] / expenses * 100
            lines.append(f"{emoji} {cat['name']} — {fmt_amount(cat['total'])}₽ ({pct:.0f}%)")

    await message.answer("\n".join(lines))


@router.message(Command("balance"))
async def cmd_balance(message: Message):
    user = get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала запустите /start")
        return

    balance = get_balance(user["id"])
    await message.answer(format_balance(balance))
