from .repository import GoalRepository

class GoalService:
    def __init__(self, repository: GoalRepository):
        self.repository = repository

    def get_goals(self, user_id):
        return self.repository.get_goals(user_id)

    def add_goal(self, user_id, name, target_amount, deadline=None):
        self.repository.add_goal(user_id, name, target_amount, deadline)

    def deposit_to_goal(self, user_id, goal_id, amount):
        self.repository.deposit_to_goal(user_id, goal_id, amount)

    def update_goal(self, user_id, goal_id, name, target_amount, deadline):
        self.repository.update_goal(goal_id, user_id, name, target_amount, deadline)

    def delete_goal(self, user_id, goal_id):
        self.repository.delete_goal(user_id, goal_id)
