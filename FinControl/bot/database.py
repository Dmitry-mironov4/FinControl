import sqlite3, os

# получаем путь к файлу базы данных
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')

# возвращает соединение с базой данных
def get_connection():
    return sqlite3.connect(DB_PATH)

# функция для создания всех таблиц
def create_tables():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # таблица с персональными данными пользователей
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

    # таблица с категориями расходов и доходов
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL CHECK(type IN ('income', 'expense'))
            )
    ''')

    # таблица с доходами пользователя
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS incomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            category_id INTEGER NOT NULL,
            description TEXT,
            date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
    ''')

    # таблица c расходами пользователя
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            category_id INTEGER NOT NULL,
            description TEXT,
            date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
    ''')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_tables()