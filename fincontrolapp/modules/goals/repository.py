import sqlite3
from datetime import date

class GoalRepository:
    def __init__(self, con: sqlite3.Connection):
        self.con = con
    
    def get_goals(self, user_id):
        return self.con.execute(
            'SELECT * FROM goals WHERE user_id = ? ORDER BY created_at DESC',
            (user_id,)
        ).fetchall()

    def add_goal(self, user_id, name, target_amount, deadline=None):
        self.con.execute(
            'INSERT INTO goals (user_id, name, target_amount, deadline) VALUES (?, ?, ?, ?)',
            (user_id, name, target_amount, deadline)
        )
    def deposit_to_goal(self, user_id, goal_id, amount):
        self.con.execute(
            'UPDATE goals SET current_amount = current_amount + ? WHERE id = ?',
            (amount, goal_id)
        )
        savings_cat = self.con.execute(
            "SELECT id FROM categories WHERE name='Накопления' AND type='expense'"
        ).fetchone()
        if savings_cat:
            self.con.execute(
                '''INSERT INTO transactions (user_id, type, amount, category_id, description, date)
                   VALUES (?, 'expense', ?, ?, 'Накопления на цель', ?)''',
                (user_id, amount, savings_cat['id'], str(date.today()))
            )

    def update_goal(self, goal_id, user_id, name, target_amount, deadline):
        self.con.execute(
            'UPDATE goals SET name=?, target_amount=?, deadline=? WHERE id=? AND user_id=?',
            (name, target_amount, deadline, goal_id, user_id)
        )

    def delete_goal(self, user_id, goal_id):
        self.con.execute(
            'DELETE FROM goals WHERE id = ? AND user_id = ?',
            (goal_id, user_id)
        )