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


def get_transactions(user_id, type_=None, category_id=None, limit=None, offset=0):
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
        query += ' LIMIT ? OFFSET ?'
        params.extend([limit, offset])

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


def delete_transaction(transaction_id: int, user_id: int | None = None) -> bool:
    with get_connection() as conn:
        if user_id is not None:
            cursor = conn.execute(
                'DELETE FROM transactions WHERE id = ? AND user_id = ?',
                (transaction_id, user_id)
            )
        else:
            cursor = conn.execute(
                'DELETE FROM transactions WHERE id = ?',
                (transaction_id,)
            )
        return cursor.rowcount > 0


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
            'UPDATE goals SET current_amount = current_amount + ? WHERE id = ? AND user_id = ?',
            (amount, goal_id, user_id)
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


# ─── Настройки уведомлений ────────────────────────────────────────────────────

def get_notification_hour(user_id: int) -> int:
    """Возвращает час уведомлений пользователя (0–23, default 9)."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT notification_hour FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    return int(row["notification_hour"]) if row and row["notification_hour"] is not None else 9


def set_notification_hour(user_id: int, hour: int) -> None:
    """Установить час ежедневных уведомлений (0–23)."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET notification_hour = ? WHERE id = ?", (hour, user_id)
        )
        conn.commit()


def get_users_to_notify(hour: int) -> list:
    """Все привязанные пользователи, у которых notification_hour == hour."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM users WHERE telegram_id IS NOT NULL AND notification_hour = ?",
            (hour,),
        ).fetchall()
    return [dict(r) for r in rows]


# ─── Таймеры покупок ──────────────────────────────────────────────────────────

def get_active_timers(user_id: int) -> list:
    """Активные таймеры: решение ещё не принято."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT id, item_name, amount, remind_at, notified
               FROM purchase_timers
               WHERE user_id = ? AND decision IS NULL
               ORDER BY remind_at ASC""",
            (user_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def create_purchase_timer(user_id: int, item_name: str, amount: float, remind_at: str) -> int:
    """
    Создать таймер покупки.
    remind_at — строка ISO 8601: 'YYYY-MM-DD HH:MM:SS'
    Возвращает id новой записи.
    """
    with get_connection() as conn:
        cursor = conn.execute(
            """INSERT INTO purchase_timers (user_id, item_name, amount, remind_at)
               VALUES (?, ?, ?, ?)""",
            (user_id, item_name, amount, remind_at),
        )
        conn.commit()
        return cursor.lastrowid


def get_due_purchase_timers() -> list:
    """Таймеры, по которым пора отправить уведомление: remind_at <= now, notified=0."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT pt.id, pt.user_id, pt.item_name, pt.amount, u.telegram_id
               FROM purchase_timers pt
               JOIN users u ON u.id = pt.user_id
               WHERE pt.notified = 0
                 AND pt.decision IS NULL
                 AND pt.remind_at <= datetime('now', 'localtime')
                 AND u.telegram_id IS NOT NULL""",
        ).fetchall()
    return [dict(r) for r in rows]


def mark_purchase_timer_notified(timer_id: int) -> None:
    """Пометить таймер как отправленный (notified=1)."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE purchase_timers SET notified = 1 WHERE id = ?",
            (timer_id,),
        )
        conn.commit()


def set_purchase_timer_decision(timer_id: int, decision: str) -> None:
    """
    Записать решение пользователя.
    decision: 'bought' | 'cancelled'
    """
    with get_connection() as conn:
        conn.execute(
            "UPDATE purchase_timers SET decision = ? WHERE id = ?",
            (decision, timer_id),
        )
        conn.commit()


# ─── Проверка превышения бюджета ──────────────────────────────────────────────

def get_budget_exceeded_info(user_id: int, category_id: int) -> dict | None:
    """
    Проверяет, превышен ли лимит бюджета по категории за текущий месяц.
    Возвращает None если лимита нет или расход < 90% лимита.
    Возвращает dict {'category_name', 'limit', 'spent', 'pct'} если >= 90%.
    """
    from datetime import date
    today = date.today()
    start = today.replace(day=1).isoformat()
    end = today.isoformat()

    with get_connection() as conn:
        budget = conn.execute(
            "SELECT limit_amount FROM budgets WHERE user_id = ? AND category_id = ? AND period = 'monthly'",
            (user_id, category_id),
        ).fetchone()
        if not budget:
            return None

        limit = float(budget["limit_amount"])
        row = conn.execute(
            """SELECT COALESCE(SUM(amount), 0) AS spent
               FROM transactions
               WHERE user_id = ? AND category_id = ? AND type = 'expense'
                 AND date BETWEEN ? AND ?""",
            (user_id, category_id, start, end),
        ).fetchone()
        spent = float(row["spent"])
        pct = spent / limit * 100 if limit > 0 else 0

        if pct < 90:
            return None

        cat = conn.execute(
            "SELECT name FROM categories WHERE id = ?", (category_id,)
        ).fetchone()

    return {
        "category_name": cat["name"] if cat else "Категория",
        "limit": limit,
        "spent": spent,
        "pct": pct,
    }


if __name__ == "__main__":
    create_tables()
    print(f"База данных создана: {DB_PATH}")
