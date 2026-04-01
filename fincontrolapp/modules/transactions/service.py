from .repository import TransactionRepository


class TransactionService:
    def __init__(self, repository: TransactionRepository):
        self.repository = repository

    def add_transaction(self, user_id, type_, amount, category_id, description, date, is_recurring=0):
        self.repository.add_transaction(user_id, type_, amount, category_id, description, date, is_recurring)

    def get_transactions(self, user_id, type_=None, category_id=None, limit=None):
        return self.repository.get_transactions(user_id, type_, category_id, limit)

    def delete_transaction(self, transaction_id):
        self.repository.delete_transaction(transaction_id)

    def update_transaction(self, transaction_id, amount, date):
        self.repository.update_transaction(transaction_id, amount, date)

    def get_balance(self, user_id):
        row = self.repository.get_balance(user_id)
        return (row['total_income'] or 0) - (row['total_expense'] or 0)
    
    def get_monthly_balance(self, user_id, year, month):
        row = self.repository.get_monthly_balance(user_id, year, month)
        return (row['total_income'] or 0) - (row['total_expense'] or 0)