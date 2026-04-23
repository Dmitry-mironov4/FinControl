from datetime import date
import calendar
import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # доступ к полям по имени: row['amount']
    return conn


def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    # пользователи
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            email TEXT UNIQUE,
            phone TEXT UNIQUE,
            username TEXT,
            password_hash TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # категории доходов и расходов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('income', 'expense'))
        )
    ''')

    # транзакции (доходы и расходы)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
            amount DECIMAL(10,2) NOT NULL,
            category_id INTEGER NOT NULL,
            description TEXT,
            date DATE NOT NULL,
            is_recurring INTEGER DEFAULT 0,  -- 1 = повторяющийся (зарплата)
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    ''')

    # финансовые цели
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            target_amount DECIMAL(10,2) NOT NULL,
            current_amount DECIMAL(10,2) DEFAULT 0,
            deadline DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # подписки
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            charge_day INTEGER NOT NULL,  -- день месяца списания (1-31)
            period TEXT DEFAULT 'monthly' CHECK(period IN ('monthly', 'yearly')),
            start_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # миграция: добавляем start_date в subscriptions для существующих БД
    try:
        cursor.execute('ALTER TABLE subscriptions ADD COLUMN start_date DATE')
    except Exception:
        pass  # колонка уже существует

    # AUTO-2: миграция — is_paused и last_charged_at
    try:
        cursor.execute('ALTER TABLE subscriptions ADD COLUMN is_paused INTEGER DEFAULT 0')
    except Exception:
        pass
    try:
        cursor.execute('ALTER TABLE subscriptions ADD COLUMN last_charged_at DATE')
    except Exception:
        pass

    # стартовые категории
    cursor.execute("SELECT COUNT(*) FROM categories")
    if cursor.fetchone()[0] == 0:
        default_categories = [
            ('Начальный баланс', 'income'),
            ('Зарплата', 'income'),
            ('Фриланс', 'income'),
            ('Другое', 'income'),
            ('Еда', 'expense'),
            ('Транспорт', 'expense'),
            ('Здоровье', 'expense'),
            ('Покупки', 'expense'),
            ('Развлечения', 'expense'),
            ('Жильё', 'expense'),
            ('Образование', 'expense'),
            ('Накопления', 'expense'),
            ('Другое', 'expense'),
        ]
        cursor.executemany(
            "INSERT INTO categories (name, type) VALUES (?, ?)",
            default_categories
        )
    else:
        # добавляем категорию Накопления если её нет
        cursor.execute("SELECT id FROM categories WHERE name='Накопления' AND type='expense'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO categories (name, type) VALUES ('Накопления', 'expense')")
        # AUTO-2: категория Подписки
        cursor.execute("SELECT id FROM categories WHERE name='Подписки' AND type='expense'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO categories (name, type) VALUES ('Подписки', 'expense')")

    conn.commit()
    conn.close()


# ─── ПОЛЬЗОВАТЕЛИ ─────────────────────────────────────────────────────────────

def get_user_by_telegram_id(telegram_id: int):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
    ).fetchone()
    conn.close()
    return row


def get_user_by_id(user_id: int):
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM users WHERE id = ?", (user_id,)
    ).fetchone()
    conn.close()
    return row


def create_user(telegram_id: int, username: str | None, phone: str | None) -> int:
    conn = get_connection()
    cursor = conn.execute(
        "INSERT INTO users (telegram_id, username, phone) VALUES (?, ?, ?)",
        (telegram_id, username, phone),
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_id


def update_user_phone(telegram_id: int, phone: str) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE users SET phone = ? WHERE telegram_id = ?", (phone, telegram_id)
    )
    conn.commit()
    conn.close()


def link_telegram_to_user_by_id(user_id: int, telegram_id: int) -> bool:
    """Привязывает telegram_id к существующему пользователю. Возвращает False если уже занято."""
    conn = get_connection()
    existing = conn.execute(
        "SELECT id FROM users WHERE telegram_id = ? AND id != ?", (telegram_id, user_id)
    ).fetchone()
    if existing:
        conn.close()
        return False
    conn.execute(
        "UPDATE users SET telegram_id = ? WHERE id = ?", (telegram_id, user_id)
    )
    conn.commit()
    conn.close()
    return True


def get_all_linked_users():
    """Все пользователи с привязанным Telegram."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM users WHERE telegram_id IS NOT NULL"
    ).fetchall()
    conn.close()
    return rows


# ─── ТРАНЗАКЦИИ ───────────────────────────────────────────────────────────────

def add_transaction(user_id, type_, amount, category_id, description, date, is_recurring=0):
    with get_connection() as conn:
        cursor = conn.execute(
            '''INSERT INTO transactions (user_id, type, amount, category_id, description, date, is_recurring)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (user_id, type_, amount, category_id, description, date, is_recurring)
        )
        return cursor.lastrowid


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


def get_last_transactions(user_id: int, limit: int = 10, offset: int = 0):
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT t.*, c.name AS category_name
        FROM transactions t
        LEFT JOIN categories c ON c.id = t.category_id
        WHERE t.user_id = ?
        ORDER BY t.date DESC, t.created_at DESC
        LIMIT ? OFFSET ?
        """,
        (user_id, limit, offset),
    ).fetchall()
    conn.close()
    return rows


def delete_transaction(transaction_id, user_id=None):
    with get_connection() as conn:
        if user_id is not None:
            conn.execute(
                'DELETE FROM transactions WHERE id = ? AND user_id = ?',
                (transaction_id, user_id)
            )
        else:
            conn.execute('DELETE FROM transactions WHERE id = ?', (transaction_id,))


def update_transaction(transaction_id, amount, date):
    with get_connection() as conn:
        conn.execute(
            'UPDATE transactions SET amount=?, date=? WHERE id=?',
            (amount, date, transaction_id)
        )


# ─── БАЛАНС ───────────────────────────────────────────────────────────────────

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
               GROUP BY month ORDER BY month DESC LIMIT ?''',
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


def get_monthly_stats(user_id: int, year: int, month: int) -> dict:
    conn = get_connection()
    row = conn.execute(
        """
        SELECT
            COALESCE(SUM(CASE WHEN type='income'  THEN amount ELSE 0 END), 0) AS income,
            COALESCE(SUM(CASE WHEN type='expense' THEN amount ELSE 0 END), 0) AS expenses
        FROM transactions
        WHERE user_id = ?
          AND strftime('%Y', date) = ?
          AND strftime('%m', date) = ?
        """,
        (user_id, str(year), f"{month:02d}"),
    ).fetchone()
    conn.close()
    return {"income": float(row["income"]), "expenses": float(row["expenses"])}


def get_monthly_summary(user_id: int) -> dict:
    """Доходы и расходы за текущий месяц."""
    import datetime as _dt
    today = _dt.date.today()
    return get_monthly_stats(user_id, today.year, today.month)


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


if __name__ == "__main__":
    create_tables()
    print(f"База данных создана: {DB_PATH}")
