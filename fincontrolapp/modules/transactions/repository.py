import calendar
import sqlite3
from .model import Transaction # noqa: F401

class TransactionRepository:
    def __init__(self, con: sqlite3.Connection):
        self.con = con

    def add_transaction(self, user_id, type_, amount, category_id, description, date, is_recurring=0):
        self.con.execute(
            '''INSERT INTO transactions (user_id, type, amount, category_id, description, date, is_recurring)
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (user_id, type_, amount, category_id, description, date, is_recurring)
        )


    def get_transactions(self, user_id, type_=None, category_id=None, limit=None):
        query = '''
            SELECT t.id, t.type, t.amount, t.description, t.date, t.is_recurring,
                t.category_id, c.name as category_name
            FROM transactions t
            JOIN categories c ON t.category_id = c.id
            WHERE t.user_id = ?
        '''
        params = [user_id]
        if type_:
            query += ' AND t.type = ?'
            params.append(type_)
        if category_id:
            query += ' AND t.category_id = ?'
            params.append(category_id)
        query += ' ORDER BY t.date DESC, t.id DESC'
        if limit:
            query += ' LIMIT ?'
            params.append(limit)

        return self.con.execute(query, tuple(params)).fetchall()

    def delete_transaction(self, transaction_id):
        self.con.execute('DELETE FROM transactions WHERE id = ?', (transaction_id,))


    def update_transaction(self, transaction_id, type_, amount, category_id, description, date):
        self.con.execute(
            'UPDATE transactions SET type=?, amount=?, category_id=?, description=?, date=? WHERE id=?',
            (type_, amount, category_id, description, date, transaction_id)
        )

    def get_balance(self, user_id):
        row = self.con.execute(
            '''SELECT
                SUM(CASE WHEN type='income' THEN amount ELSE 0 END) as total_income,
                SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) as total_expense
                FROM transactions WHERE user_id = ?''',
            (user_id,)
        ).fetchone()
        return row
    
    def get_monthly_balance(self, user_id, year, month):
        start_date = f"{year}-{month:02d}-01"
        last_day = calendar.monthrange(year, month)[1]
        end_date = f"{year}-{month:02d}-{last_day:02d}"
        row = self.con.execute(
            '''SELECT
                SUM(CASE WHEN type='income' THEN amount ELSE 0 END) as total_income,
                SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) as total_expense
                FROM transactions 
                WHERE user_id = ? AND date BETWEEN ? AND ?''',
            (user_id, start_date, end_date)
        ).fetchone()
        return row
    
    def get_recurring_income_for_month(self, user_id: int, year: int, month: int):
        # Проверяет, была ли уже добавлена recurring-зарплата за указанный месяц
        return self.con.execute(
            '''SELECT id FROM transactions
            WHERE user_id = ? AND type='income' AND is_recurring=1
            AND strftime('%Y-%m', date) = ?''',
            (user_id, f"{year:04d}-{month:02d}")
        ).fetchall()

    def get_last_recurring_income(self, user_id: int):
        # Возвращает последнюю зарплату (шаблон) для копирования суммы, категории и описания
        return self.con.execute(
            '''SELECT amount, category_id, description FROM transactions
            WHERE user_id = ? AND type='income' AND is_recurring=1
            ORDER BY date DESC LIMIT 1''',
            (user_id,)
        ).fetchone()