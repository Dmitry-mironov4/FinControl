"""Tests for notification jobs.

These are dry-run tests: they do not hit Telegram, but they prove the jobs
call `send_message()` when the data conditions are met.
"""

import asyncio
import datetime

from bot.handlers import notify


class FakeBot:
    def __init__(self):
        self.messages = []

    async def send_message(self, chat_id, text, **kwargs):
        self.messages.append({"chat_id": chat_id, "text": text, "kwargs": kwargs})


def test_notify_user_sends_all_expected_messages(monkeypatch):
    bot = FakeBot()
    fixed_today = datetime.date(2026, 5, 11)
    tomorrow = fixed_today + datetime.timedelta(days=1)

    class FixedDate(datetime.date):
        @classmethod
        def today(cls):
            return fixed_today

    monkeypatch.setattr(notify.datetime, "date", FixedDate)

    monkeypatch.setattr(notify, "get_notify_prefs", lambda user_id: {
        "notify_subscriptions": 1,
        "notify_goals": 1,
        "notify_budget": 1,
    })
    monkeypatch.setattr(notify, "get_subscriptions", lambda user_id: [
        {"name": "Netflix", "amount": 499.0, "charge_day": tomorrow.day},
    ])
    monkeypatch.setattr(notify, "get_goals", lambda user_id: [
        {"name": "MacBook", "current_amount": 100.0, "target_amount": 1000.0},
    ])
    monkeypatch.setattr(notify, "get_monthly_stats", lambda user_id, year, month: {
        "income": 1000.0,
        "expenses": 850.0,
    })

    asyncio.run(notify._notify_user(bot, {"telegram_id": 123, "id": 1}))

    assert len(bot.messages) == 3
    assert any("Завтра спишется" in msg["text"] for msg in bot.messages)
    assert any("Прогресс по целям" in msg["text"] for msg in bot.messages)
    assert any("Потрачено" in msg["text"] for msg in bot.messages)


def test_timer_job_sends_due_timer_notification(monkeypatch):
    bot = FakeBot()
    marked = []

    monkeypatch.setattr(notify, "get_due_purchase_timers", lambda: [
        {"id": 7, "telegram_id": 123, "item_name": "Кофе", "amount": 250.0},
    ])
    monkeypatch.setattr(notify, "mark_purchase_timer_notified", lambda timer_id: marked.append(timer_id))

    asyncio.run(notify._timer_job(bot))

    assert len(bot.messages) == 1
    assert "Кофе" in bot.messages[0]["text"]
    assert marked == [7]


def test_hourly_job_calls_user_notification_for_matching_hour(monkeypatch):
    called = []
    current_hour = datetime.datetime.now().hour

    monkeypatch.setattr(notify, "get_users_to_notify", lambda hour: [
        {"id": 1, "telegram_id": 123, "notification_hour": current_hour},
    ] if hour == current_hour else [])

    async def fake_notify_user(bot, user):
        called.append(user["id"])

    monkeypatch.setattr(notify, "_notify_user", fake_notify_user)

    asyncio.run(notify._hourly_job(FakeBot()))

    assert called == [1]
