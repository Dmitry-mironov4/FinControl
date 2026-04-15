from datetime import date
from modules.subscriptions.repository import SubscriptionRepository
from modules.subscriptions.service import SubscriptionService
from database import get_connection


class SubscriptionsController:
    def __init__(self, user_id: int):
        self._user_id = user_id

    def get_subscriptions(self):
        with get_connection() as con:
            return SubscriptionService(SubscriptionRepository(con)).get_subscriptions(self._user_id)

    def get_monthly_total(self) -> float:
        with get_connection() as con:
            return SubscriptionService(SubscriptionRepository(con)).get_monthly_total(self._user_id)

    def add_subscription(self, name: str, amount: float, charge_day: int,
                         period: str = 'monthly', start_date: str | None = None):
        with get_connection() as con:
            SubscriptionService(SubscriptionRepository(con)).add_subscription(
                self._user_id, name, amount, charge_day, period,
                start_date or str(date.today())
            )

    def update_subscription(self, subscription_id: int, name: str, amount: float,
                            charge_day: int, period: str, start_date: str):
        with get_connection() as con:
            SubscriptionService(SubscriptionRepository(con)).update_subscription(
                subscription_id, name, amount, charge_day, period, start_date
            )

    def delete_subscription(self, subscription_id: int):
        with get_connection() as con:
            SubscriptionService(SubscriptionRepository(con)).delete_subscription(subscription_id)

    @staticmethod
    def calc_next_charge_date(charge_day: int, period: str,
                               start_date_str: str | None = None) -> date:
        return SubscriptionService.calc_next_charge_date(charge_day, period, start_date_str)
