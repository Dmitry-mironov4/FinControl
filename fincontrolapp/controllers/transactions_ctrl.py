from modules.transactions.repository import TransactionRepository
from modules.transactions.service import TransactionService
from modules.categories.repository import CategoryRepository
from modules.categories.service import CategoryService
from database import get_connection


class TransactionsController:
    def __init__(self, user_id: int):
        self._user_id = user_id

    def get_transactions(self, type_=None):
        with get_connection() as con:
            return TransactionService(TransactionRepository(con)).get_transactions(
                self._user_id, type_=type_
            )

    def get_categories(self, type_=None):
        with get_connection() as con:
            return CategoryService(CategoryRepository(con)).get_all(type_=type_)

    def add_transaction(self, type_: str, amount: float, category_id: int,
                        description: str | None, date: str):
        with get_connection() as con:
            TransactionService(TransactionRepository(con)).add_transaction(
                self._user_id, type_, amount, category_id, description, date
            )

    def delete_transaction(self, transaction_id: int):
        with get_connection() as con:
            TransactionService(TransactionRepository(con)).delete_transaction(transaction_id)

    def update_transaction(self, transaction_id: int, type_: str, amount: float,
                           category_id: int, description: str | None, date: str):
        with get_connection() as con:
            TransactionService(TransactionRepository(con)).update_transaction(
                transaction_id, type_, amount, category_id, description, date
            )
