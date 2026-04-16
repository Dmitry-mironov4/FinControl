import datetime
import calendar
import logging
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot.utils.formatters import fmt_amount
from fincontrolapp.db_queries import (
    get_all_linked_users,
    get_subscriptions,
    get_goals,
    get_monthly_stats,
)

logger = logging.getLogger(__name__)


def _months_until(deadline_str: str) -> float:
    """Return months remaining until deadline (float). Returns 12 if no deadline."""
    if not deadline_str:
        return 12.0
    try:
        deadline = datetime.date.fromisoformat(deadline_str)
        today = datetime.date.today()
        delta_days = (deadline - today).days
        return max(delta_days / 30.0, 1.0)
    except ValueError:
        return 12.0


async def notify_subscriptions(bot: Bot) -> None:
    """Daily at 10:00 — warn about subscriptions charging tomorrow."""
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)
    tomorrow_day = tomorrow.day

    users = get_all_linked_users()
    for user in users:
        tg_id = user["telegram_id"]
        subs = get_subscriptions(user["id"])
        due = [
            s for s in subs
            if s["charge_day"] == tomorrow_day
        ]
        if not due:
            continue

        lines = []
        for s in due:
            lines.append(
                f"⚠️ Напоминание!\n"
                f"Завтра спишется {fmt_amount(float(s['amount']))}₽ за {s['name']}.\n"
                f"Убедись что на карте достаточно средств."
            )

        try:
            await bot.send_message(tg_id, "\n\n".join(lines))
        except Exception as e:
            logger.warning("Failed to send subscription reminder to %s: %s", tg_id, e)


async def notify_goals(bot: Bot) -> None:
    """Every Monday — remind about active goals."""
    today = datetime.date.today()

    users = get_all_linked_users()
    for user in users:
        tg_id = user["telegram_id"]
        goals = get_goals(user["id"])
        active = [
            g for g in goals
            if float(g["current_amount"]) < float(g["target_amount"])
        ]
        if not active:
            continue

        buttons = []
        lines = ["🎯 Не забудь про цели!", ""]

        for g in active:
            target = float(g["target_amount"])
            current = float(g["current_amount"])
            remaining = target - current
            months = _months_until(g.get("deadline"))
            monthly = remaining / months

            lines.append(f"На «{g['name']}» нужно откладывать ~{fmt_amount(monthly)}₽/мес.")
            buttons.append([
                InlineKeyboardButton(
                    text=f"💰 Пополнить «{g['name']}»",
                    callback_data=f"goal_deposit_{g['id']}"
                )
            ])

        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        try:
            await bot.send_message(tg_id, "\n".join(lines), reply_markup=keyboard)
        except Exception as e:
            logger.warning("Failed to send goals reminder to %s: %s", tg_id, e)


async def notify_budget(bot: Bot) -> None:
    """Weekly — warn if expenses exceed 80% of income."""
    today = datetime.date.today()

    users = get_all_linked_users()
    for user in users:
        tg_id = user["telegram_id"]
        stats = get_monthly_stats(user["id"], today.year, today.month)
        income = stats["income"]
        expenses = stats["expenses"]

        if income <= 0 or expenses / income < 0.8:
            continue

        pct = expenses / income * 100
        days_in_month = calendar.monthrange(today.year, today.month)[1]
        days_left = days_in_month - today.day
        remaining = max(income - expenses, 0)

        text = (
            f"📊 Внимание!\n"
            f"В этом месяце ты уже потратил {pct:.0f}% доходов.\n"
            f"Осталось: {fmt_amount(remaining)}₽ и {days_left} дней до конца месяца."
        )
        try:
            await bot.send_message(tg_id, text)
        except Exception as e:
            logger.warning("Failed to send budget warning to %s: %s", tg_id, e)
