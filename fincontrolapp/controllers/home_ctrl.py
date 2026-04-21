from datetime import date
from modules.transactions.repository import TransactionRepository
from modules.transactions.service import TransactionService
from database import get_connection


class HomeController:
    def __init__(self, user_id: int):
        self._user_id = user_id

    def get_balance(self) -> dict:
        with get_connection() as con:
            row = TransactionRepository(con).get_balance(self._user_id)
        income = row['total_income'] or 0
        expense = row['total_expense'] or 0
        return {'income': income, 'expense': expense, 'balance': income - expense}

    def get_monthly_balance(self) -> dict:
        today = date.today()
        with get_connection() as con:
            row = TransactionRepository(con).get_monthly_balance(self._user_id, today.year, today.month)
        return {'income': row['total_income'] or 0, 'expense': row['total_expense'] or 0}

    def get_recent_transactions(self, limit: int = 5):
        with get_connection() as con:
            return TransactionService(TransactionRepository(con)).get_transactions(
                self._user_id, limit=limit
            )

    def save_initial_balance(self, amount: float) -> None:
        """Сохраняет или обновляет начальный баланс пользователя (upsert)."""
        from datetime import date as _date
        today = str(_date.today())
        with get_connection() as con:
            cat = con.execute(
                "SELECT id FROM categories WHERE name='Начальный баланс'"
            ).fetchone()
            if not cat:
                raise ValueError("Категория 'Начальный баланс' не найдена")
            TransactionRepository(con).upsert_initial_balance(
                user_id=self._user_id,
                amount=amount,
                category_id=cat['id'],
                date=today,
            )
