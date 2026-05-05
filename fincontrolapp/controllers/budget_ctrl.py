from modules.budgets.service import BudgetService
from modules.budgets.model import Budget


class BudgetController:
    def __init__(self, user_id: int):
        self._service = BudgetService(user_id)

    def get_budgets(self, period: str = 'monthly') -> list[Budget]:
        return self._service.get_budgets(period)

    def set_budget(self, category_id: int, limit_amount: float, period: str = 'monthly') -> None:
        self._service.set_budget(category_id, limit_amount, period)

    def delete_budget(self, budget_id: int) -> None:
        self._service.delete_budget(budget_id)

    def get_expense_categories(self) -> list[dict]:
        return self._service.get_expense_categories()