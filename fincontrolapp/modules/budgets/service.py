from database import get_connection
from .repository import BudgetRepository
from .model import Budget


class BudgetService:
    def __init__(self, user_id: int):
        self._user_id = user_id

    def get_budgets(self, period: str = 'monthly') -> list[Budget]:
        with get_connection() as con:
            repo = BudgetRepository(con)
            return repo.get_budgets_with_spent(self._user_id, period)

    def set_budget(self, category_id: int, limit_amount: float, period: str = 'monthly') -> None:
        with get_connection() as con:
            repo = BudgetRepository(con)
            repo.upsert(self._user_id, category_id, limit_amount, period)
            con.commit()

    def delete_budget(self, budget_id: int) -> None:
        with get_connection() as con:
            repo = BudgetRepository(con)
            repo.delete(budget_id, self._user_id)
            con.commit()

    def get_expense_categories(self) -> list[dict]:
        with get_connection() as con:
            repo = BudgetRepository(con)
            return repo.get_expense_categories(self._user_id)

    def check_budget_exceeded(self, category_id: int, period: str = 'monthly') -> dict | None:
        """
        Проверяет, превышен ли лимит по категории.
        Возвращает None если лимита нет или лимит не превышен.
        Возвращает dict {'category_name': ..., 'limit': ..., 'spent': ..., 'pct': ...} если превышен.
        """
        with get_connection() as con:
            repo = BudgetRepository(con)
            row = repo.get_budget_for_category(self._user_id, category_id, period)
            if not row:
                return None
            spent = repo.get_spent_for_category(self._user_id, category_id, period)
            limit = float(row["limit_amount"])
            pct = spent / limit * 100 if limit > 0 else 0
            if pct < 90:
                return None
            from database import get_connection as _gc
            with _gc() as c2:
                cat = c2.execute("SELECT name FROM categories WHERE id = ?", (category_id,)).fetchone()
            return {
                "category_name": cat["name"] if cat else "Категория",
                "limit": limit,
                "spent": spent,
                "pct": pct,
            }