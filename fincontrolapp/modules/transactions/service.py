from .repository import TransactionRepository


class TransactionService:
    def __init__(self, repository: TransactionRepository, category_repository=None):
        self.repository = repository
        self.category_repository = category_repository

    def add_transaction(self, user_id, type_, amount, category_id, description, date, is_recurring=0):
        self.repository.add_transaction(user_id, type_, amount, category_id, description, date, is_recurring)

    def get_transactions(self, user_id, type_=None, category_id=None, limit=None):
        return self.repository.get_transactions(user_id, type_, category_id, limit)

    def delete_transaction(self, transaction_id):
        self.repository.delete_transaction(transaction_id)

    def update_transaction(self, transaction_id, type_, amount, category_id, description, date):
        self.repository.update_transaction(transaction_id, type_, amount, category_id, description, date)

    def get_balance(self, user_id):
        row = self.repository.get_balance(user_id)
        return (row['total_income'] or 0) - (row['total_expense'] or 0)
    
    def get_monthly_balance(self, user_id, year, month):
        row = self.repository.get_monthly_balance(user_id, year, month)
        return (row['total_income'] or 0) - (row['total_expense'] or 0)

    def save_initial_balance(self, user_id: int, amount: float, date: str) -> None:
        """Сохраняет или обновляет начальный баланс пользователя.

        Ищет категорию 'Начальный баланс' через category_repository и делегирует
        upsert в repository. Требует, чтобы category_repository был передан
        при создании сервиса.
        """
        if self.category_repository is None:
            raise RuntimeError("category_repository не передан в TransactionService")
        cat = self.category_repository.get_by_name('Начальный баланс')
        if not cat:
            raise ValueError("Категория 'Начальный баланс' не найдена")
        self.repository.upsert_initial_balance(
            user_id=user_id,
            amount=amount,
            category_id=cat.id,
            date=date,
        )