from database import get_connection

def get_user_by_telegram_id(telegram_id):
    # Получить пользователя по telegram_id
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def create_user(telegram_id, username=None, phone=None):
    # Создать нового пользователя
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO users (telegram_id, username, phone) VALUES (?, ?, ?)",
            (telegram_id, username, phone)
        )
        conn.commit()
        return cursor.lastrowid
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def update_user_phone(telegram_id, phone):
    # Обновить телефон пользователя
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE users SET phone = ? WHERE telegram_id = ?",
            (phone, telegram_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def get_user_by_id(user_id):
    # Получить пользователя по ID
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None


def link_telegram_to_user_by_id(user_id, telegram_id):
    # Привязать telegram_id к существующему пользователю по его ID
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE users SET telegram_id = ? WHERE id = ? AND (telegram_id IS NULL OR telegram_id != ?)",
            (telegram_id, user_id, telegram_id)
        )
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()