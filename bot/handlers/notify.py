import calendar
import datetime
import logging

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from bot.utils.formatters import fmt_amount
from fincontrolapp.db_queries import get_all_linked_users, get_subscriptions, get_goals, get_monthly_stats

logger = logging.getLogger(__name__)


def _next_charge_date(charge_day: int) -> datetime.date:
    """Вычислить ближайшую дату списания для дня месяца charge_day."""
    today = datetime.date.today()
    import calendar
    last_day = calendar.monthrange(today.year, today.month)[1]
    day = min(charge_day, last_day)
    candidate = today.replace(day=day)
    if candidate <= today:
        # переходим на следующий месяц
        if today.month == 12:
            next_month = today.replace(year=today.year + 1, month=1, day=1)
        else:
            next_month = today.replace(month=today.month + 1, day=1)
        last_day_next = calendar.monthrange(next_month.year, next_month.month)[1]
        candidate = next_month.replace(day=min(charge_day, last_day_next))
    return candidate


async def _send_subscription_reminders(bot: Bot) -> None:
    """Ежедневно в 09:00 — уведомления о подписках, которые спишутся завтра."""
    tomorrow = datetime.date.today() + datetime.timedelta(days=1)

    users = get_all_linked_users()
    for user in users:
        tg_id = user["telegram_id"]
        subs = get_subscriptions(user["id"])

        due = [s for s in subs if _next_charge_date(s["charge_day"]) == tomorrow]
        if not due:
            continue

        lines = ["💳 Завтра спишется:"]
        total = 0.0
        for s in due:
            amount = float(s["amount"])
            total += amount
            lines.append(f"  • {s['name']} — {fmt_amount(amount)} ₽")
        lines.append(f"Итого: {fmt_amount(total)} ₽")

        text = "\n".join(lines)
        try:
            await bot.send_message(tg_id, text)
        except TelegramForbiddenError:
            logger.warning("Пользователь %s заблокировал бота — пропускаем", tg_id)
        except Exception as e:
            logger.warning("Не удалось отправить напоминание о подписках %s: %s", tg_id, e)


async def _send_goals_reminders(bot: Bot) -> None:
    """Еженедельно в понедельник 09:00 — напоминания о незавершённых целях."""
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

        lines = ["🎯 Напоминание о целях:"]
        for g in active:
            target = float(g["target_amount"])
            current = float(g["current_amount"])
            pct = int(current / target * 100) if target > 0 else 0
            lines.append(
                f"  • {g['name']}: {pct}% ({fmt_amount(current)} / {fmt_amount(target)} ₽)"
            )

        text = "\n".join(lines)
        try:
            await bot.send_message(tg_id, text)
        except TelegramForbiddenError:
            logger.warning("Пользователь %s заблокировал бота — пропускаем", tg_id)
        except Exception as e:
            logger.warning("Не удалось отправить напоминание о целях %s: %s", tg_id, e)


async def _send_budget_warning(bot: Bot) -> None:
    """Еженедельно — предупреждение, если расходы превысили 80% доходов."""
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
        except TelegramForbiddenError:
            logger.warning("Пользователь %s заблокировал бота — пропускаем", tg_id)
        except Exception as e:
            logger.warning("Не удалось отправить предупреждение о бюджете %s: %s", tg_id, e)


def setup_notify_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        _send_subscription_reminders,
        CronTrigger(hour=9, minute=0),
        args=[bot],
        id="notify_subscriptions",
    )

    scheduler.add_job(
        _send_goals_reminders,
        CronTrigger(day_of_week="mon", hour=9, minute=0),
        args=[bot],
        id="notify_goals",
    )

    scheduler.add_job(
        _send_budget_warning,
        CronTrigger(day_of_week="mon", hour=9, minute=0),
        args=[bot],
        id="notify_budget",
    )

    return scheduler
