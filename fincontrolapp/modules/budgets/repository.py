import sqlite3
from datetime import date
from .model import Budget


class BudgetRepository:
    def __init__(self, con: sqlite3.Connection):
        self.con = con

    def get_budgets_with_spent(self, user_id: int, period: str = 'monthly') -> list[Budget]:
        """
        Возвращает все бюджеты пользователя вместе с суммой потраченного за текущий период.
        """
        today = date.today()
        if period == 'monthly':
            start = today.replace(day=1).isoformat()
        else:
            start = today.replace(month=1, day=1).isoformat()
        end = today.isoformat()

        rows = self.con.execute(
            """SELECT b.id, b.category_id, b.limit_amount, b.period,
                      c.name AS category_name,
                      COALESCE(SUM(t.amount), 0) AS spent
               FROM budgets b
               JOIN categories c ON c.id = b.category_id
               LEFT JOIN transactions t
                   ON t.user_id = b.user_id
                  AND t.category_id = b.category_id
                  AND t.type = 'expense'
                  AND t.date BETWEEN ? AND ?
               WHERE b.user_id = ? AND b.period = ?
               GROUP BY b.id, b.category_id, b.limit_amount, b.period, c.name
               ORDER BY c.name""",
            (start, end, user_id, period),
        ).fetchall()

        return [
            Budget(
                id=r["id"],
                user_id=user_id,
                category_id=r["category_id"],
                category_name=r["category_name"],
                limit_amount=float(r["limit_amount"]),
                spent_amount=float(r["spent"]),
                period=r["period"],
            )
            for r in rows
        ]

    def upsert(self, user_id: int, category_id: int, limit_amount: float, period: str = 'monthly') -> None:
        """Создать или обновить бюджет (INSERT OR REPLACE)."""
        self.con.execute(
            """INSERT INTO budgets (user_id, category_id, limit_amount, period)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(user_id, category_id, period)
               DO UPDATE SET limit_amount = excluded.limit_amount""",
            (user_id, category_id, limit_amount, period),
        )

    def delete(self, budget_id: int, user_id: int) -> None:
        self.con.execute(
            "DELETE FROM budgets WHERE id = ? AND user_id = ?",
            (budget_id, user_id),
        )

    def get_expense_categories(self, user_id: int) -> list[dict]:
        """Возвращает все категории расходов для выбора при создании бюджета."""
        rows = self.con.execute(
            "SELECT id, name FROM categories WHERE type = 'expense' ORDER BY name",
        ).fetchall()
        return [{"id": r["id"], "name": r["name"]} for r in rows]

    def get_spent_for_category(self, user_id: int, category_id: int, period: str = 'monthly') -> float:
        """Потрачено по категории за текущий период (для проверки превышения в боте)."""
        today = date.today()
        start = today.replace(day=1).isoformat() if period == 'monthly' else today.replace(month=1, day=1).isoformat()
        row = self.con.execute(
            """SELECT COALESCE(SUM(amount), 0) AS spent
               FROM transactions
               WHERE user_id = ? AND category_id = ? AND type = 'expense'
                 AND date BETWEEN ? AND ?""",
            (user_id, category_id, start, today.isoformat()),
        ).fetchone()
        return float(row["spent"])

    def get_budget_for_category(self, user_id: int, category_id: int, period: str = 'monthly'):
        """Получить лимит бюджета по категории. Вернуть None если лимит не задан."""
        row = self.con.execute(
            "SELECT * FROM budgets WHERE user_id = ? AND category_id = ? AND period = ?",
            (user_id, category_id, period),
        ).fetchone()
        return row