from modules.goals.repository import GoalRepository
from modules.goals.service import GoalService
from database import get_connection
from datetime import date, datetime

class GoalsController:
    def __init__(self, user_id: int):
        self._user_id = user_id

    def get_goals(self):
        with get_connection() as con:
            repo = GoalRepository(con)
            service = GoalService(repo)
            return service.get_goals(self._user_id)
        
    def add_goal(self, name, target_amount, deadline=None):
        with get_connection() as con:
            repo = GoalRepository(con)
            service = GoalService(repo)
            service.add_goal(self._user_id, name, target_amount, deadline)

    def update_goal(self, goal_id, name, target_amount, deadline=None):
        with get_connection() as con:
            GoalService(GoalRepository(con)).update_goal(self._user_id, goal_id, name, target_amount, deadline)

    def delete_goal(self, goal_id):
        with get_connection() as con:
            repo = GoalRepository(con)
            service = GoalService(repo)
            service.delete_goal(self._user_id, goal_id)

    def deposit(self, goal_id, amount):
        with get_connection() as con:
            repo = GoalRepository(con)
            service = GoalService(repo)
            service.deposit_to_goal(self._user_id, goal_id, amount)

    def calc_pace(self, target, current, deadline_value):
        """Возвращает строку с темпом накоплений или None."""
        remaining = target - current
        if remaining <= 0 or not deadline_value:
            return None
        try:
            if isinstance(deadline_value, datetime):
                dl = deadline_value.date()
            elif isinstance(deadline_value, date):
                dl = deadline_value
            elif isinstance(deadline_value, str):
                dl = date.fromisoformat(deadline_value)
            else:
                return None

            days_left = (dl - date.today()).days
            if days_left <= 0:
                return "Срок истёк"
            months_left = max(days_left / 30, 1)
            per_month = remaining / months_left
            return f"Нужно: {per_month:,.0f} ₽/мес · осталось {int(months_left)} мес."
        except (ValueError, TypeError):
            return None