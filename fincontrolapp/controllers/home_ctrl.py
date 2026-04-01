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
