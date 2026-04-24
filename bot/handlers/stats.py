import datetime
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardRemove

from fincontrolapp.db_queries import get_user_by_telegram_id, get_balance, get_monthly_summary
from bot.utils.formatters import fmt_amount, MONTH_NAMES

router = Router()


@router.message(Command("help"))
async def cmd_help(message: Message):
    text = (
        "📖 Справка FinControl\n"
        "─────────────────────\n"
        "/start        — привязать аккаунт\n"
        "/stats        — баланс и статистика\n"
        "/add          — добавить транзакцию\n"
        "/history      — история операций\n"
        "/goals        — мои цели\n"
        "/subscriptions — подписки\n"
        "/help         — эта справка\n\n"
        "💡 Быстрое добавление — просто напиши:\n"
        "<code>+5000 зарплата</code>  (доход)\n"
        "<code>-300 кофе</code>       (расход)"
    )
    await message.answer(text, parse_mode="HTML")


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    user = get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала запустите /start")
        return

    month_name = MONTH_NAMES[datetime.date.today().month].capitalize()
    balance = get_balance(user["id"])
    summary = get_monthly_summary(user["id"])
    income = summary["income"]
    expenses = summary["expenses"]
    savings_rate = round((income - expenses) / income * 100) if income > 0 else 0

    text = (
        f"💰 Баланс: {fmt_amount(balance)} ₽\n"
        f"─────────────────\n"
        f"📈 Доходы ({month_name}):   {fmt_amount(income)} ₽\n"
        f"📉 Расходы ({month_name}):  {fmt_amount(expenses)} ₽\n"
        f"💼 Норма сбережений:  {savings_rate}%"
    )
    await message.answer(text)
