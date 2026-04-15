from datetime import date
from .repository import SubscriptionRepository


class SubscriptionService:
    def __init__(self, repository: SubscriptionRepository):
        self.repository = repository

    def get_subscriptions(self, user_id: int):
        return self.repository.get_all(user_id)

    def get_monthly_total(self, user_id: int) -> float:
        return self.repository.get_monthly_total(user_id)

    def add_subscription(self, user_id: int, name: str, amount: float,
                         charge_day: int, period: str = 'monthly',
                         start_date: str | None = None):
        self.repository.add(user_id, name, amount, charge_day, period, start_date)

    def update_subscription(self, subscription_id: int, name: str, amount: float,
                            charge_day: int, period: str, start_date: str):
        self.repository.update(subscription_id, name, amount, charge_day, period, start_date)

    def delete_subscription(self, subscription_id: int):
        self.repository.delete(subscription_id)

    @staticmethod
    def calc_next_charge_date(charge_day: int, period: str,
                               start_date_str: str | None = None) -> date:
        return SubscriptionRepository.calc_next_charge_date(charge_day, period, start_date_str)
