from datetime import date, datetime, timedelta
import calendar
import re
import secrets

try:
    from fincontrolapp.database import DB_PATH, create_tables as _create_tables, get_connection as _get_connection
except ImportError:
    from database import DB_PATH, create_tables as _create_tables, get_connection as _get_connection


def normalize_phone(phone: str) -> str:
    """Приводит телефон к формату +7XXXXXXXXXX."""
    digits = re.sub(r'\D', '', phone)
    if len(digits) == 11 and digits[0] in ('7', '8'):
        digits = '7' + digits[1:]
    elif len(digits) == 10:
        digits = '7' + digits
    return '+' + digits if digits else phone


def get_connection():
    return _get_connection()


def create_tables():
    return _create_tables()


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
        (telegram_id, username, normalize_phone(phone) if phone else None),
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return user_id


def update_user_phone(telegram_id: int, phone: str) -> None:
    conn = get_connection()
    conn.execute(
        "UPDATE users SET phone = ? WHERE telegram_id = ?", (normalize_phone(phone), telegram_id)
    )
    conn.commit()
    conn.close()


def request_password_reset(user_id: int) -> bool:
    """Генерирует временный пароль, сохраняет хэш и plain для отправки ботом.
    Возвращает False если у пользователя нет привязанного Telegram."""
    import string
    from pages.auth import hash_password
    with get_connection() as conn:
        row = conn.execute(
            'SELECT telegram_id FROM users WHERE id=?', (user_id,)
        ).fetchone()
        if not row or not row['telegram_id']:
            return False
        alphabet = string.ascii_letters + string.digits
        temp_pwd = ''.join(secrets.choice(alphabet) for _ in range(10))
        conn.execute(
            'UPDATE users SET password_hash=?, reset_password=? WHERE id=?',
            (hash_password(temp_pwd), temp_pwd, user_id)
        )
    return True


def get_users_pending_reset() -> list:
    """Пользователи с ожидающим сбросом пароля (для бота)."""
    with get_connection() as conn:
        rows = conn.execute(
            'SELECT id, telegram_id, reset_password FROM users '
            'WHERE reset_password IS NOT NULL AND telegram_id IS NOT NULL'
        ).fetchall()
    return [dict(r) for r in rows]


def clear_reset_password(user_id: int) -> None:
    with get_connection() as conn:
        conn.execute('UPDATE users SET reset_password=NULL WHERE id=?', (user_id,))


def change_password(user_id: int, old_pwd: str, new_pwd: str) -> bool:
    """Меняет пароль после проверки старого. Возвращает False если старый неверный."""
    from pages.auth import hash_password, verify_password
    with get_connection() as conn:
        row = conn.execute(
            'SELECT password_hash FROM users WHERE id=?', (user_id,)
        ).fetchone()
        if not row or not verify_password(row['password_hash'], old_pwd):
            return False
        conn.execute(
            'UPDATE users SET password_hash=? WHERE id=?',
            (hash_password(new_pwd), user_id)
        )
    return True


def get_user_by_contact(contact: str) -> dict | None:
    """Ищет пользователя по email или телефону (с нормализацией номера)."""
    phone_norm = normalize_phone(contact) if re.search(r'\d{7,}', contact) else contact
    with get_connection() as conn:
        row = conn.execute(
            'SELECT id, telegram_id FROM users WHERE email=? OR phone=?',
            (contact, phone_norm)
        ).fetchone()
    return dict(row) if row else None


def generate_link_token(user_id: int) -> str:
    """Генерирует одноразовый токен привязки Telegram (действует 15 минут)."""
    token = secrets.token_urlsafe(16)
    expires_at = (datetime.now() + timedelta(minutes=15)).strftime('%Y-%m-%d %H:%M:%S')
    with get_connection() as conn:
        conn.execute(
            'UPDATE users SET link_token=?, link_token_expires_at=? WHERE id=?',
            (token, expires_at, user_id)
        )
    return token


def link_telegram_by_token(token: str, telegram_id: int) -> dict | None:
    """Привязывает telegram_id к аккаунту по токену. Возвращает пользователя или None."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM users WHERE link_token=? AND link_token_expires_at > datetime('now', 'localtime')",
            (token,)
        ).fetchone()
        if not row:
            return None
        existing = conn.execute(
            "SELECT id FROM users WHERE telegram_id=? AND id!=?", (telegram_id, row['id'])
        ).fetchone()
        if existing:
            return None
        conn.execute(
            'UPDATE users SET telegram_id=?, link_token=NULL, link_token_expires_at=NULL WHERE id=?',
            (telegram_id, row['id'])
        )
    return dict(row)


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


def delete_transaction(transaction_id: int, user_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.execute(
            'DELETE FROM transactions WHERE id = ? AND user_id = ?',
            (transaction_id, user_id)
        )
        return cursor.rowcount > 0


def update_transaction(transaction_id: int, amount: float, date, user_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.execute(
            'UPDATE transactions SET amount=?, date=? WHERE id=? AND user_id=?',
            (amount, date, transaction_id, user_id)
        )
        return cursor.rowcount > 0



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
        cursor = conn.execute(
            'UPDATE goals SET current_amount = current_amount + ? WHERE id = ? AND user_id = ?',
            (amount, goal_id, user_id)
        )
        if cursor.rowcount == 0:
            return False
        savings_cat = conn.execute(
            "SELECT id FROM categories WHERE name='Накопления' AND type='expense'"
        ).fetchone()
        if savings_cat:
            conn.execute(
                '''INSERT INTO transactions (user_id, type, amount, category_id, description, date)
                   VALUES (?, 'expense', ?, ?, 'Накопления на цель', ?)''',
                (user_id, amount, savings_cat['id'], str(date.today()))
            )
        return True


def delete_goal(goal_id: int, user_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.execute(
            'DELETE FROM goals WHERE id = ? AND user_id = ?',
            (goal_id, user_id)
        )
        return cursor.rowcount > 0


# ─── ПОДПИСКИ ─────────────────────────────────────────────────────────────────

def get_subscriptions(user_id):
    with get_connection() as conn:
        return conn.execute(
            'SELECT * FROM subscriptions WHERE user_id = ? AND (is_paused IS NULL OR is_paused = 0) ORDER BY charge_day',
            (user_id,)
        ).fetchall()


def get_subscriptions_monthly_total(user_id):
    with get_connection() as conn:
        row = conn.execute(
            '''SELECT SUM(CASE WHEN period='monthly' THEN amount
                              WHEN period='yearly' THEN amount/12.0
                         END) as total
               FROM subscriptions
               WHERE user_id = ? AND (is_paused IS NULL OR is_paused = 0)''',
            (user_id,)
        ).fetchone()
    return row['total'] or 0


def add_subscription(user_id, name, amount, charge_day, period='monthly', start_date=None):
    with get_connection() as conn:
        conn.execute(
            'INSERT INTO subscriptions (user_id, name, amount, charge_day, period, start_date) VALUES (?, ?, ?, ?, ?, ?)',
            (user_id, name, amount, charge_day, period, start_date)
        )


def delete_subscription(subscription_id: int, user_id: int) -> bool:
    with get_connection() as conn:
        cursor = conn.execute(
            'DELETE FROM subscriptions WHERE id = ? AND user_id = ?',
            (subscription_id, user_id)
        )
        return cursor.rowcount > 0


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


def get_notify_prefs(user_id: int) -> dict:
    """Возвращает настройки типов уведомлений (1=вкл, 0=выкл)."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT notify_subscriptions, notify_goals, notify_budget FROM users WHERE id = ?",
            (user_id,)
        ).fetchone()
    if not row:
        return {"notify_subscriptions": 1, "notify_goals": 1, "notify_budget": 1}
    return {
        "notify_subscriptions": int(row["notify_subscriptions"] if row["notify_subscriptions"] is not None else 1),
        "notify_goals": int(row["notify_goals"] if row["notify_goals"] is not None else 1),
        "notify_budget": int(row["notify_budget"] if row["notify_budget"] is not None else 1),
    }


def set_notify_prefs(user_id: int, notify_subscriptions: int, notify_goals: int, notify_budget: int) -> None:
    """Сохранить настройки типов уведомлений."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET notify_subscriptions=?, notify_goals=?, notify_budget=? WHERE id=?",
            (notify_subscriptions, notify_goals, notify_budget, user_id)
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


def delete_purchase_timer(timer_id: int, user_id: int) -> None:
    """Удалить таймер покупки (только свой)."""
    with get_connection() as conn:
        conn.execute(
            "DELETE FROM purchase_timers WHERE id = ? AND user_id = ?",
            (timer_id, user_id),
        )
        conn.commit()


def get_active_purchase_timers(user_id: int) -> list:
    """Активные таймеры пользователя: без решения и без уведомления (ещё ждут)."""
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT id, item_name, amount, remind_at
               FROM purchase_timers
               WHERE user_id = ?
                 AND decision IS NULL
               ORDER BY remind_at ASC""",
            (user_id,),
        ).fetchall()
    return [dict(r) for r in rows]


def get_purchase_timer(timer_id: int) -> dict | None:
    """Вернуть один таймер по id."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM purchase_timers WHERE id = ?", (timer_id,)
        ).fetchone()
    return dict(row) if row else None


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


# ─── Настройки валюты ────────────────────────────────────────────────────────

def get_user_currency(user_id: int) -> tuple:
    """Возвращает (display_currency, currency_conversion, secondary_currency) для пользователя.

    display_currency   — код валюты отображения, напр. 'USD'
    currency_conversion — 'as_is' или 'convert'
    secondary_currency — код второй валюты или None
    """
    with get_connection() as conn:
        row = conn.execute(
            "SELECT display_currency, currency_conversion, secondary_currency FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    if not row:
        return ("RUB", "as_is", None)
    return (
        row["display_currency"] or "RUB",
        row["currency_conversion"] or "as_is",
        row["secondary_currency"] or None,
    )


def set_user_currency(user_id: int, display_currency: str, currency_conversion: str,
                      secondary_currency: str | None = None) -> None:
    """Сохранить настройки отображения валюты."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE users SET display_currency = ?, currency_conversion = ?, secondary_currency = ? WHERE id = ?",
            (display_currency, currency_conversion, secondary_currency, user_id),
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
