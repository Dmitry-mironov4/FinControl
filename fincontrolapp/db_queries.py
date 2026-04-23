from datetime import date
import calendar
from database import get_connection


# ─── ТРАНЗАКЦИИ ───────────────────────────────────────────────────────────────

def add_transaction(user_id, type_, amount, category_id, description, date, is_recurring=0):
    with get_connection() as conn:
        conn.execute(
            '''INSERT INTO transactions (user_id, type, amount, category_id, description, date, is_recurring)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (user_id, type_, amount, category_id, description, date, is_recurring)
        )


def get_transactions(user_id, type_=None, category_id=None, limit=None):
    query = '''
        SELECT t.id, t.type, t.amount, t.description, t.date, t.is_recurring,
               c.name as category_name
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
    query += ' ORDER BY t.date DESC'
    if limit:
        query += ' LIMIT ?'
        params.append(limit)

    with get_connection() as conn:
        return conn.execute(query, params).fetchall()


def delete_transaction(transaction_id):
    with get_connection() as conn:
        conn.execute('DELETE FROM transactions WHERE id = ?', (transaction_id,))


def update_transaction(transaction_id, amount, date):
    with get_connection() as conn:
        conn.execute(
            'UPDATE transactions SET amount=?, date=? WHERE id=?',
            (amount, date, transaction_id)
        )


# ─── БАЛАНС (для Home) ────────────────────────────────────────────────────────

def get_balance(user_id):
    with get_connection() as conn:
        row = conn.execute(
            '''SELECT
                SUM(CASE WHEN type='income' THEN amount ELSE 0 END) as total_income,
                SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) as total_expense
               FROM transactions WHERE user_id = ?''',
            (user_id,)
        ).fetchone()
    income = row['total_income'] or 0
    expense = row['total_expense'] or 0
    return {'income': income, 'expense': expense, 'balance': income - expense}


def get_monthly_balance(user_id, year: int, month: int):
    month_str = f"{year:04d}-{month:02d}"
    with get_connection() as conn:
        row = conn.execute(
            '''SELECT
                SUM(CASE WHEN type='income' THEN amount ELSE 0 END) as income,
                SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) as expense
               FROM transactions
               WHERE user_id = ? AND strftime('%Y-%m', date) = ?''',
            (user_id, month_str)
        ).fetchone()
    return {
        'income': row['income'] or 0,
        'expense': row['expense'] or 0,
    }


# ─── АНАЛИТИКА ────────────────────────────────────────────────────────────────

def get_monthly_data(user_id, months=6):
    with get_connection() as conn:
        return conn.execute(
            '''SELECT strftime('%Y-%m', date) as month,
                      SUM(CASE WHEN type='income' THEN amount ELSE 0 END) as income,
                      SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) as expense
               FROM transactions WHERE user_id = ?
               GROUP BY month ORDER BY month ASC LIMIT ?''',
            (user_id, months)
        ).fetchall()


def get_expense_breakdown(user_id):
    with get_connection() as conn:
        return conn.execute(
            '''SELECT c.name, SUM(t.amount) as total
               FROM transactions t
               JOIN categories c ON t.category_id = c.id
               WHERE t.user_id = ? AND t.type = 'expense'
               GROUP BY c.name ORDER BY total DESC''',
            (user_id,)
        ).fetchall()


# ─── КАТЕГОРИИ ────────────────────────────────────────────────────────────────

def get_categories(type_=None):
    query = 'SELECT * FROM categories'
    params = []
    if type_:
        query += ' WHERE type = ?'
        params.append(type_)
    with get_connection() as conn:
        return conn.execute(query, params).fetchall()


# ─── ЦЕЛИ ─────────────────────────────────────────────────────────────────────

def get_goals(user_id):
    with get_connection() as conn:
        return conn.execute(
            'SELECT * FROM goals WHERE user_id = ? ORDER BY created_at DESC',
            (user_id,)
        ).fetchall()


def add_goal(user_id, name, target_amount, deadline=None):
    with get_connection() as conn:
        conn.execute(
            'INSERT INTO goals (user_id, name, target_amount, deadline) VALUES (?, ?, ?, ?)',
            (user_id, name, target_amount, deadline)
        )


def deposit_to_goal(user_id, goal_id, amount):
    """Пополняет цель и создаёт расход с категорией Накопления."""
    with get_connection() as conn:
        conn.execute(
            'UPDATE goals SET current_amount = current_amount + ? WHERE id = ?',
            (amount, goal_id)
        )
        savings_cat = conn.execute(
            "SELECT id FROM categories WHERE name='Накопления' AND type='expense'"
        ).fetchone()
        if savings_cat:
            conn.execute(
                '''INSERT INTO transactions (user_id, type, amount, category_id, description, date)
                   VALUES (?, 'expense', ?, ?, 'Накопления на цель', ?)''',
                (user_id, amount, savings_cat['id'], str(date.today()))
            )


def delete_goal(goal_id):
    with get_connection() as conn:
        conn.execute('DELETE FROM goals WHERE id = ?', (goal_id,))


# ─── ПОДПИСКИ ─────────────────────────────────────────────────────────────────

def get_subscriptions(user_id):
    with get_connection() as conn:
        return conn.execute(
            'SELECT * FROM subscriptions WHERE user_id = ? ORDER BY charge_day',
            (user_id,)
        ).fetchall()


def get_subscriptions_monthly_total(user_id):
    with get_connection() as conn:
        row = conn.execute(
            '''SELECT SUM(CASE WHEN period='monthly' THEN amount
                              WHEN period='yearly' THEN amount/12.0
                         END) as total
               FROM subscriptions WHERE user_id = ?''',
            (user_id,)
        ).fetchone()
    return row['total'] or 0


def add_subscription(user_id, name, amount, charge_day, period='monthly', start_date=None):
    with get_connection() as conn:
        conn.execute(
            'INSERT INTO subscriptions (user_id, name, amount, charge_day, period, start_date) VALUES (?, ?, ?, ?, ?, ?)',
            (user_id, name, amount, charge_day, period, start_date)
        )


def delete_subscription(subscription_id):
    with get_connection() as conn:
        conn.execute('DELETE FROM subscriptions WHERE id = ?', (subscription_id,))


def get_next_charge_date(charge_day: int, period: str, start_date_str: str | None = None) -> date:
    """Вычисляет следующую дату списания подписки."""
    today = date.today()
    year, month = today.year, today.month

    # ближайший charge_day в этом или следующем месяце
    max_day = calendar.monthrange(year, month)[1]
    day = min(charge_day, max_day)
    candidate = date(year, month, day)

    if period == 'monthly':
        if candidate <= today:
            # переходим на следующий месяц
            if month == 12:
                year, month = year + 1, 1
            else:
                month += 1
            max_day = calendar.monthrange(year, month)[1]
            day = min(charge_day, max_day)
            candidate = date(year, month, day)
    elif period == 'yearly' and start_date_str:
        try:
            sd = date.fromisoformat(start_date_str)
            # следующая годовщина
            candidate = date(today.year, sd.month, min(sd.day, calendar.monthrange(today.year, sd.month)[1]))
            if candidate <= today:
                candidate = date(today.year + 1, sd.month, min(sd.day, calendar.monthrange(today.year + 1, sd.month)[1]))
        except ValueError:
            pass

    return candidate
