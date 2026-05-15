"""
seed_demo.py — Демо-данные для MVP Demo (25 апреля 2026)

Запуск из корня проекта:
    python scripts/seed_demo.py

Создаёт тестового пользователя и заполняет 4 месяца данных:
- Транзакции (доходы + расходы по категориям)
- 3 подписки
- 2 цели накоплений
- Начальный баланс

Логин: demo@fincontrol.ru / demo1234
"""

import sqlite3
import hashlib
import os
import sys
from datetime import date, timedelta

# ─── Путь к БД ───────────────────────────────────────────────────────────────
# Запускать из корня проекта: python scripts/seed_demo.py
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH  = os.path.join(BASE_DIR, "fincontrolapp", "database.db")

if not os.path.exists(DB_PATH):
    print(f"[ERROR] БД не найдена: {DB_PATH}")
    print("Сначала запустите приложение, чтобы создать таблицы.")
    sys.exit(1)

# ─── Хеширование пароля (совместимо с auth.py) ───────────────────────────────
def hash_password(password: str) -> str:
    salt = bytes.fromhex("a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6")  # фиксированная соль для воспроизводимости
    key  = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100000)
    return salt.hex() + ":" + key.hex()

# ─── Подключение ─────────────────────────────────────────────────────────────
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur  = conn.cursor()

print("=" * 50)
print("  FinControl — Seed Demo Data")
print("=" * 50)

# ─── Очистка старого демо-пользователя ───────────────────────────────────────
existing = cur.execute(
    "SELECT id FROM users WHERE email='demo@fincontrol.ru'"
).fetchone()

if existing:
    uid = existing["id"]
    print(f"[INFO] Старый демо-пользователь найден (id={uid}), очищаю данные...")
    cur.execute("DELETE FROM transactions   WHERE user_id=?", (uid,))
    cur.execute("DELETE FROM goals          WHERE user_id=?", (uid,))
    cur.execute("DELETE FROM subscriptions  WHERE user_id=?", (uid,))
    cur.execute("DELETE FROM users          WHERE id=?",      (uid,))
    conn.commit()

# ─── Создать пользователя ────────────────────────────────────────────────────
cur.execute(
    "INSERT INTO users (email, username, password_hash) VALUES (?, ?, ?)",
    ("demo@fincontrol.ru", "Дмитрий", hash_password("demo1234"))
)
conn.commit()
user_id = cur.lastrowid
print(f"[OK] Пользователь создан: id={user_id}, email=demo@fincontrol.ru, пароль=demo1234")

# ─── Получить id категорий ───────────────────────────────────────────────────
def cat(name: str, type_: str) -> int:
    row = cur.execute(
        "SELECT id FROM categories WHERE name=? AND type=?", (name, type_)
    ).fetchone()
    if not row:
        print(f"[WARN] Категория '{name}' ({type_}) не найдена, буду использовать 'Другое'")
        row = cur.execute(
            "SELECT id FROM categories WHERE name='Другое' AND type=?", (type_,)
        ).fetchone()
    return row["id"]

# ─── Даты: последние 4 месяца ─────────────────────────────────────────────────
today  = date.today()

def d(month_offset: int, day: int) -> str:
    """Дата: месяц назад + день. month_offset=0 → текущий месяц."""
    year  = today.year
    month = today.month - month_offset
    if month <= 0:
        month += 12
        year  -= 1
    # Защита от дней вроде 31 февраля
    import calendar
    last_day = calendar.monthrange(year, month)[1]
    day = min(day, last_day)
    return date(year, month, day).isoformat()

# ─── ТРАНЗАКЦИИ ──────────────────────────────────────────────────────────────
transactions = [

    # ── ЯНВАРЬ (3 месяца назад) ──────────────────────────────────────────────
    # Доходы
    ("income",  65000, "Зарплата",      "Зарплата за январь",        d(3,  5)),
    ("income",   8500, "Фриланс",       "Верстка сайта для клиента", d(3, 18)),
    # Расходы
    ("expense",  3200, "Еда",           "Пятёрочка, Магнит",         d(3,  7)),
    ("expense",  4100, "Еда",           "ВкусВилл и рынок",          d(3, 15)),
    ("expense",  1800, "Еда",           "Кафе, обеды",               d(3, 22)),
    ("expense",  3500, "Транспорт",     "Проездной на месяц",        d(3,  5)),
    ("expense",   900, "Транспорт",     "Такси",                     d(3, 20)),
    ("expense",  2400, "Здоровье",      "Аптека + врач",             d(3, 12)),
    ("expense", 15000, "Жильё",         "Аренда комнаты",            d(3,  1)),
    ("expense",  3800, "Покупки",       "Одежда",                    d(3, 25)),
    ("expense",  1200, "Развлечения",   "Кино, концерт",             d(3, 28)),
    ("expense",  2500, "Образование",   "Курс по Python",            d(3, 10)),
    ("expense",  5000, "Накопления",    "Накопления на цель",        d(3, 30)),

    # ── ФЕВРАЛЬ (2 месяца назад) ─────────────────────────────────────────────
    ("income",  65000, "Зарплата",      "Зарплата за февраль",       d(2,  5)),
    ("income",  12000, "Фриланс",       "Разработка бота",           d(2, 22)),
    ("expense",  3600, "Еда",           "Супермаркеты",              d(2,  8)),
    ("expense",  3900, "Еда",           "Еда за неделю",             d(2, 16)),
    ("expense",  2100, "Еда",           "Рестораны и кафе",          d(2, 24)),
    ("expense",  3500, "Транспорт",     "Проездной",                 d(2,  5)),
    ("expense",  1500, "Транспорт",     "Каршеринг",                 d(2, 19)),
    ("expense", 15000, "Жильё",         "Аренда",                    d(2,  1)),
    ("expense",  8900, "Покупки",       "Техника — наушники",        d(2, 14)),  # аномалия
    ("expense",  1600, "Развлечения",   "Стриминг + игры",           d(2, 28)),
    ("expense",  5000, "Накопления",    "Накопления на цель",        d(2, 28)),

    # ── МАРТ (1 месяц назад) ─────────────────────────────────────────────────
    ("income",  65000, "Зарплата",      "Зарплата за март",          d(1,  5)),
    ("income",   5000, "Другое",        "Возврат долга",             d(1, 11)),
    ("expense",  3800, "Еда",           "Магнит, Перекрёсток",       d(1,  9)),
    ("expense",  4200, "Еда",           "Закупка на неделю",         d(1, 17)),
    ("expense",  1900, "Еда",           "Обеды в кампусе",           d(1, 25)),
    ("expense",  3500, "Транспорт",     "Проездной",                 d(1,  5)),
    ("expense",   700, "Транспорт",     "Такси ночью",               d(1, 22)),
    ("expense", 15000, "Жильё",         "Аренда",                    d(1,  1)),
    ("expense",  4500, "Покупки",       "Спортивный инвентарь",      d(1, 20)),
    ("expense",  2800, "Здоровье",      "Стоматолог",                d(1, 13)),
    ("expense",  1400, "Развлечения",   "Боулинг с друзьями",        d(1, 29)),
    ("expense",  2500, "Образование",   "Учебники",                  d(1, 10)),
    ("expense",  7000, "Накопления",    "Накопления на цель",        d(1, 31)),

    # ── АПРЕЛЬ (текущий месяц) ───────────────────────────────────────────────
    ("income",  65000, "Зарплата",      "Зарплата за апрель",        d(0,  5)),
    ("expense",  3400, "Еда",           "Пятёрочка",                 d(0,  7)),
    ("expense",  1700, "Еда",           "Кофейня, завтраки",         d(0, 12)),
    ("expense",  3500, "Транспорт",     "Проездной",                 d(0,  5)),
    ("expense", 15000, "Жильё",         "Аренда",                    d(0,  1)),
    ("expense",  3200, "Покупки",       "Весенняя куртка",           d(0, 18)),
    ("expense",  1100, "Развлечения",   "Подписка на кино",          d(0, 20)),
    ("expense",  5000, "Накопления",    "Накопления на цель",        d(0, 22)),
]

for type_, amount, cat_name, desc, tx_date in transactions:
    cat_id = cat(cat_name, type_)
    cur.execute(
        """INSERT INTO transactions (user_id, type, amount, category_id, description, date)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (user_id, type_, amount, cat_id, desc, tx_date)
    )

conn.commit()
print(f"[OK] Транзакций добавлено: {len(transactions)}")

# ─── ПОДПИСКИ ────────────────────────────────────────────────────────────────
subscriptions = [
    ("Яндекс Плюс",   299,  1, "monthly", d(0, 1)),
    ("Spotify",       199, 15, "monthly", d(0, 1)),
    ("ChatGPT Plus", 1900, 20, "monthly", d(0, 1)),
]

for name, amount, charge_day, period, start_date in subscriptions:
    cur.execute(
        """INSERT INTO subscriptions (user_id, name, amount, charge_day, period, start_date)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (user_id, name, amount, charge_day, period, start_date)
    )

conn.commit()
print(f"[OK] Подписок добавлено: {len(subscriptions)}")

# ─── ЦЕЛИ ────────────────────────────────────────────────────────────────────
goals = [
    ("MacBook Pro M3",  180000, 27000, "2026-12-31"),
    ("Отпуск в Турции",  60000, 15000, "2026-07-01"),
]

for name, target, current, deadline in goals:
    cur.execute(
        """INSERT INTO goals (user_id, name, target_amount, current_amount, deadline)
           VALUES (?, ?, ?, ?, ?)""",
        (user_id, name, target, current, deadline)
    )

conn.commit()
print(f"[OK] Целей добавлено: {len(goals)}")

# ─── Итоговый баланс ─────────────────────────────────────────────────────────
row = conn.execute(
    """SELECT
           SUM(CASE WHEN type='income'  THEN amount ELSE 0 END) AS inc,
           SUM(CASE WHEN type='expense' THEN amount ELSE 0 END) AS exp
       FROM transactions WHERE user_id=?""",
    (user_id,)
).fetchone()

balance = (row["inc"] or 0) - (row["exp"] or 0)

conn.close()

print()
print("=" * 50)
print("  ДАННЫЕ ДЛЯ ДЕМО")
print("=" * 50)
print(f"  Логин:    demo@fincontrol.ru")
print(f"  Пароль:   demo1234")
print(f"  Баланс:   {balance:,.0f} ₽".replace(",", " "))
print()
print("  ТРАНЗАКЦИИ (для показа):")
print("  Январь: зарплата 65 000 + фриланс 8 500")
print("  Февраль: зарплата 65 000 + фриланс 12 000 | аномалия: наушники 8 900")
print("  Март: зарплата 65 000 + возврат 5 000")
print("  Апрель: зарплата 65 000 (текущий месяц)")
print()
print("  ПОДПИСКИ:")
print("  • Яндекс Плюс — 299 ₽/мес, 1-го числа")
print("  • Spotify      — 199 ₽/мес, 15-го числа")
print("  • ChatGPT Plus — 1 900 ₽/мес, 20-го числа")
print("  Итого: 2 398 ₽/мес (3.7% от дохода — норма)")
print()
print("  ЦЕЛИ:")
print("  • MacBook Pro M3: 27 000 / 180 000 ₽ (15%) · срок 31.12.2026")
print("  • Отпуск в Турции: 15 000 / 60 000 ₽ (25%) · срок 01.07.2026")
print()
print("  СИМУЛЯТОР — примеры для показа:")
print("  SIM-1 Покупка: сумма=25000, дней до зарплаты=13, дневной расход=1800")
print(f"        → хватит ли: {'да' if balance >= 25000 else 'нет'}, остаток={(balance-25000):,.0f} ₽".replace(",", " "))
print("  SIM-2 Новая подписка: +990 ₽/мес (Notion)")
print("        → норма сбережений изменится с ~25% до ~23%")
print("  SIM-3 Цель: MacBook, текущие накопления 27 000, экономия ~7 000/мес")
print("        → осталось ~22 месяца")
print()
print("[ГОТОВО] Запустите приложение и войдите: demo@fincontrol.ru / demo1234")
print("=" * 50)