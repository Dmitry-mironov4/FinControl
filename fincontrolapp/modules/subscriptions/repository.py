import sqlite3
import calendar
from datetime import date


class SubscriptionRepository:
    def __init__(self, con: sqlite3.Connection):
        self.con = con

    def get_all(self, user_id: int):
        return self.con.execute(
            'SELECT * FROM subscriptions WHERE user_id = ? ORDER BY charge_day',
            (user_id,)
        ).fetchall()

    def get_monthly_total(self, user_id: int) -> float:
        row = self.con.execute(
            """SELECT SUM(CASE WHEN period='monthly' THEN amount
                              WHEN period='yearly'  THEN amount / 12.0
                         END) AS total
               FROM subscriptions WHERE user_id = ?""",
            (user_id,)
        ).fetchone()
        return row['total'] or 0.0

    def add(self, user_id: int, name: str, amount: float,
            charge_day: int, period: str = 'monthly', start_date: str | None = None):
        self.con.execute(
            'INSERT INTO subscriptions (user_id, name, amount, charge_day, period, start_date) '
            'VALUES (?, ?, ?, ?, ?, ?)',
            (user_id, name, amount, charge_day, period, start_date)
        )

    def update(self, subscription_id: int, name: str, amount: float,
               charge_day: int, period: str, start_date: str):
        self.con.execute(
            'UPDATE subscriptions SET name=?, amount=?, charge_day=?, period=?, start_date=? WHERE id=?',
            (name, amount, charge_day, period, start_date, subscription_id)
        )

    def delete(self, subscription_id: int):
        self.con.execute(
            'DELETE FROM subscriptions WHERE id = ?',
            (subscription_id,)
        )

    @staticmethod
    def calc_next_charge_date(charge_day: int, period: str,
                               start_date_str: str | None = None) -> date:
        today = date.today()
        year, month = today.year, today.month

        max_day = calendar.monthrange(year, month)[1]
        day = min(charge_day, max_day)
        candidate = date(year, month, day)

        if period == 'monthly':
            if candidate <= today:
                if month == 12:
                    year, month = year + 1, 1
                else:
                    month += 1
                max_day = calendar.monthrange(year, month)[1]
                candidate = date(year, month, min(charge_day, max_day))
        elif period == 'yearly' and start_date_str:
            try:
                sd = date.fromisoformat(start_date_str)
                candidate = date(today.year, sd.month,
                                 min(sd.day, calendar.monthrange(today.year, sd.month)[1]))
                if candidate <= today:
                    candidate = date(today.year + 1, sd.month,
                                     min(sd.day, calendar.monthrange(today.year + 1, sd.month)[1]))
            except ValueError:
                pass

        return candidate
