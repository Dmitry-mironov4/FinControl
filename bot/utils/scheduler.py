from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from bot.utils.notifications import notify_subscriptions, notify_goals, notify_budget


def setup_scheduler(bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()

    # 5.1 Subscription reminders — every day at 10:00
    scheduler.add_job(
        notify_subscriptions,
        CronTrigger(hour=10, minute=0),
        args=[bot],
        id="subscription_reminders",
    )

    # 5.2 Goals reminders — every Monday at 10:00
    scheduler.add_job(
        notify_goals,
        CronTrigger(day_of_week="mon", hour=10, minute=0),
        args=[bot],
        id="goals_reminders",
    )

    # 5.3 Budget warnings — every Monday at 10:05
    scheduler.add_job(
        notify_budget,
        CronTrigger(day_of_week="mon", hour=10, minute=5),
        args=[bot],
        id="budget_warnings",
    )

    return scheduler
