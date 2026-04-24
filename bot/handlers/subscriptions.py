import calendar
import datetime
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from fincontrolapp.db_queries import get_user_by_telegram_id, get_subscriptions
from bot.utils.formatters import fmt_amount, MONTH_SHORT

router = Router()


def _next_charge_date(charge_day: int) -> str:
    today = datetime.date.today()

    last_day_this = calendar.monthrange(today.year, today.month)[1]
    day_this = min(charge_day, last_day_this)
    candidate = today.replace(day=day_this)

    if candidate < today:
        if today.month == 12:
            next_year, next_month = today.year + 1, 1
        else:
            next_year, next_month = today.year, today.month + 1
        last_day_next = calendar.monthrange(next_year, next_month)[1]
        day_next = min(charge_day, last_day_next)
        candidate = datetime.date(next_year, next_month, day_next)

    return f"{candidate.day} {MONTH_SHORT[candidate.month]}"


@router.message(Command("subscriptions"))
async def cmd_subscriptions(message: Message):
    user = get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала запустите /start")
        return

    subs = get_subscriptions(user["id"])
    if not subs:
        await message.answer(
            "У вас нет активных подписок.\n"
            "Добавьте подписку в приложении FinControl."
        )
        return

    total = sum(float(s["amount"]) / 12 if s["period"] == "yearly" else float(s["amount"]) for s in subs)
    lines = ["📋 Активные подписки:", ""]
    for s in subs:
        next_date = _next_charge_date(s["charge_day"])
        period = "/год" if s["period"] == "yearly" else "/мес"
        lines.append(f"• {s['name']} — {fmt_amount(float(s['amount']))}₽{period} · спишется {next_date}")

    lines.append("")
    lines.append(f"Итого в месяц: {fmt_amount(total)}₽")

    await message.answer("\n".join(lines))
