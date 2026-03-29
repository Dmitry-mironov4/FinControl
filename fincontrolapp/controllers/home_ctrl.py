from datetime import date
from db_queries import get_balance, get_monthly_balance, get_transactions

class HomeController:
    def __init__(self, user_id: int):
        self._user_id = user_id

    def get_balance(self):
        return get_balance(self._user_id)

    def get_monthly_balance(self):
        today = date.today()
        return get_monthly_balance(self._user_id, today.year, today.month)

    def get_recent_transactions(self, limit=5):
        return get_transactions(self._user_id, limit=limit)
