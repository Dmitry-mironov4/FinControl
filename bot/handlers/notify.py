import asyncio
import calendar
import datetime
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from bot.utils.formatters import fmt_amount
from fincontrolapp.db_queries import (
    get_all_linked_users,
    get_subscriptions,
    get_goals,
    get_monthly_stats,
    get_due_purchase_timers,
    mark_purchase_timer_notified,
    get_users_to_notify,
)
from bot.handlers.purchase_timer import make_decision_keyboard

logger = logging.getLogger(__name__)


def _next_charge_date(charge_day: int) -> datetime.date:
    today = datetime.date.today()
    last_day = calendar.monthrange(today.year, today.month)[1]
    day = min(charge_day, last_day)
    candidate = today.replace(day=day)
    if candidate <= today:
        if today.month == 12:
            next_month = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month = today.replace(month=today.month + 1, day=1)
        last_day_next = calendar.monthrange(next_month.year, next_month.month)[1]
        candidate = next_month.replace(day=min(charge_day, last_day_next))
    return candidate


async def _notify_user(bot: Bot, user: dict) -> None:
    """
    Отправляет все актуальные уведомления одному пользователю.
    Вызывается каждый час для пользователей, у которых notification_hour совпадает.
    """
    tg_id = user["telegram_id"]
    user_id = user["id"]
    today = datetime.date.today()
    tomorrow = today + datetime.timedelta(days=1)
    messages = []

    # 1. Подписки, которые спишутся завтра
    subs = get_subscriptions(user_id)
    due_subs = [s for s in subs if _next_charge_date(s["charge_day"]) == tomorrow]
    if due_subs:
        lines = ["💳 Завтра спишется:"]
        total = 0.0
        for s in due_subs:
            amount = float(s["amount"])
            total += amount
            lines.append(f"  • {s['name']} — {fmt_amount(amount)} ₽")
        lines.append(f"Итого: {fmt_amount(total)} ₽")
        messages.append("\n".join(lines))

    # 2. Цели (только по понедельникам)
    if today.weekday() == 0:
        goals = get_goals(user_id)
        active = [g for g in goals if float(g["current_amount"]) < float(g["target_amount"])]
        if active:
            lines = ["🎯 Прогресс по целям:"]
            for g in active:
                target = float(g["target_amount"])
                current = float(g["current_amount"])
                pct = int(current / target * 100) if target > 0 else 0
                lines.append(f"  • {g['name']}: {pct}% ({fmt_amount(current)} / {fmt_amount(target)} ₽)")
            messages.append("\n".join(lines))

    # 3. Перерасход бюджета (только по понедельникам)
    if today.weekday() == 0:
        stats = get_monthly_stats(user_id, today.year, today.month)
        income = stats["income"]
        expenses = stats["expenses"]
        if income > 0 and expenses / income >= 0.8:
            pct = expenses / income * 100
            days_left = calendar.monthrange(today.year, today.month)[1] - today.day
            remaining = max(income - expenses, 0)
            messages.append(
                f"📊 Внимание! Потрачено {pct:.0f}% доходов за месяц.\n"
                f"Осталось: {fmt_amount(remaining)} ₽ и {days_left} дней."
            )

    for text in messages:
        try:
            await bot.send_message(tg_id, text)
        except TelegramForbiddenError:
            logger.warning("Пользователь %s заблокировал бота", tg_id)
        except Exception as e:
            logger.warning("Ошибка при отправке уведомления %s: %s", tg_id, e)


async def _hourly_job(bot: Bot) -> None:
    """
    Запускается каждый час.
    Отправляет уведомления пользователям, у которых notification_hour == текущий час.
    Также проверяет созревшие таймеры покупок.
    """
    current_hour = datetime.datetime.now().hour

    # уведомления пользователям по их времени
    users = await asyncio.to_thread(get_users_to_notify, current_hour)
    for user in users:
        await _notify_user(bot, user)

    # таймеры покупок
    timers = await asyncio.to_thread(get_due_purchase_timers)
    for t in timers:
        try:
            await bot.send_message(
                t["telegram_id"],
                f"🛍 Ты всё ещё хочешь *{t['item_name']}* за *{t['amount']:,.0f} ₽*?",
                parse_mode="Markdown",
                reply_markup=make_decision_keyboard(t["id"]),
            )
            await asyncio.to_thread(mark_purchase_timer_notified, t["id"])
        except TelegramForbiddenError:
            logger.warning("Пользователь %s заблокировал бота", t["telegram_id"])
        except Exception as e:
            logger.warning("Ошибка при отправке таймера %s: %s", t["id"], e)


def setup_notify_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        _hourly_job,
        "interval",
        hours=1,
        args=[bot],
        id="hourly_notifications",
    )

    return scheduler
