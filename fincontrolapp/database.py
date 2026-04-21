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


if __name__ == "__main__":
    create_tables()
    print(f"База данных создана: {DB_PATH}")
