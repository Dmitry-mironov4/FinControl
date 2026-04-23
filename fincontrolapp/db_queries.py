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


# ──────────────────────────────────────────────────────────────────────────────
# Функции для Telegram-бота
# ──────────────────────────────────────────────────────────────────────────────

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


def get_balance(user_id: int) -> float:
    conn = get_connection()
    row = conn.execute(
        """
        SELECT
            COALESCE(SUM(CASE WHEN type='income'  THEN amount ELSE 0 END), 0) -
            COALESCE(SUM(CASE WHEN type='expense' THEN amount ELSE 0 END), 0) AS balance
        FROM transactions
        WHERE user_id = ?
        """,
        (user_id,),
    ).fetchone()
    conn.close()
    return float(row["balance"]) if row else 0.0


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


def get_subscriptions(user_id: int):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM subscriptions WHERE user_id = ? ORDER BY charge_day",
        (user_id,),
    ).fetchall()
    conn.close()
    return rows


def get_goals(user_id: int):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM goals WHERE user_id = ? ORDER BY created_at",
        (user_id,),
    ).fetchall()
    conn.close()
    return rows


def get_categories(type: str | None = None):
    conn = get_connection()
    if type:
        rows = conn.execute(
            "SELECT * FROM categories WHERE type = ? ORDER BY name", (type,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM categories ORDER BY type, name"
        ).fetchall()
    conn.close()
    return rows


def add_transaction(
    user_id: int,
    type: str,
    amount: float,
    category_id: int,
    description: str | None,
    date,
) -> int:
    import datetime as _dt
    if isinstance(date, _dt.date):
        date = date.isoformat()
    conn = get_connection()
    cursor = conn.execute(
        """
        INSERT INTO transactions (user_id, type, amount, category_id, description, date)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (user_id, type, amount, category_id, description, date),
    )
    tx_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return tx_id


def delete_transaction(tx_id: int, user_id: int | None = None) -> bool:
    conn = get_connection()
    if user_id is not None:
        cursor = conn.execute(
            "DELETE FROM transactions WHERE id = ? AND user_id = ?", (tx_id, user_id)
        )
    else:
        cursor = conn.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
    deleted = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return deleted


def deposit_to_goal(goal_id: int, amount: float) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE goals SET current_amount = current_amount + ? WHERE id = ?",
        (amount, goal_id),
    )
    conn.commit()
    conn.close()


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


if __name__ == "__main__":
    create_tables()
    print(f"База данных создана: {DB_PATH}")