from modules.transactions.repository import TransactionRepository
from modules.transactions.service import TransactionService
from modules.categories.repository import CategoryRepository
from modules.categories.service import CategoryService
from database import get_connection


class IncomeController:
    def __init__(self, user_id: int):
        self._user_id = user_id

    def get_categories(self):
        with get_connection() as con:
            return CategoryService(CategoryRepository(con)).get_all(type_='income')

    def get_transactions(self):
        with get_connection() as con:
            return TransactionService(TransactionRepository(con)).get_transactions(
                self._user_id, type_='income'
            )

    def get_salary(self):
        transactions = self.get_transactions()
        recurring = [t for t in transactions if t['is_recurring']]
        return recurring[0] if recurring else None

    def add_transaction(self, amount: float, category_id: int,
                        description: str | None, date: str, is_recurring: int = 0):
        with get_connection() as con:
            TransactionService(TransactionRepository(con)).add_transaction(
                self._user_id, 'income', amount, category_id, description, date, is_recurring
            )

    def update_transaction(self, transaction_id: int, amount: float,
                           category_id: int, description: str | None, date: str):
        with get_connection() as con:
            TransactionService(TransactionRepository(con)).update_transaction(
                transaction_id, 'income', amount, category_id, description, date
            )

    def delete_transaction(self, transaction_id: int):
        with get_connection() as con:
            TransactionService(TransactionRepository(con)).delete_transaction(transaction_id)
