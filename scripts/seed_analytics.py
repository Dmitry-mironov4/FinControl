"""
Seed-скрипт: вставляет тестовые транзакции за 2024-2025 для user_id=1.
Запуск: uv run python scripts/seed_analytics.py
Удаление: uv run python scripts/seed_analytics.py --clear
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "fincontrolapp"))
from database import get_connection

USER_ID = 1

# category_id → name (expense)
CAT_EDA      = 5   # Еда
CAT_TRANS    = 6   # Транспорт
CAT_HEALTH   = 7   # Здоровье
CAT_SHOP     = 8   # Покупки
CAT_ENT      = 9   # Развлечения
CAT_ZHILYO   = 10  # Жильё
CAT_EDU      = 11  # Образование
CAT_SAVINGS  = 12  # Накопления
CAT_OTHER_EX = 13  # Другое (expense)
CAT_SUBS     = 14  # Подписки

# category_id → name (income)
CAT_SALARY   = 2   # Зарплата
CAT_FREELANCE= 3   # Фриланс
CAT_OTHER_IN = 4   # Другое (income)

# Данные по месяцам: (год, месяц) → список (тип, category_id, сумма, описание)
# Зарплата растёт: 85к → 90к → 95к → 100к
# Фриланс — нерегулярно
# Расходы постепенно растут с небольшими всплесками

MONTHLY_DATA = {
    # ──────────── 2024 ────────────
    (2024, 1): [
        ("income",  CAT_SALARY,   85000, "Зарплата январь"),
        ("expense", CAT_ZHILYO,   25000, "Аренда"),
        ("expense", CAT_EDA,       9800, "Продукты"),
        ("expense", CAT_TRANS,     3200, "Метро + такси"),
        ("expense", CAT_SUBS,      1500, "Подписки"),
        ("expense", CAT_ENT,       2500, "Кино"),
        ("expense", CAT_SAVINGS,  10000, "Накопления"),
    ],
    (2024, 2): [
        ("income",  CAT_SALARY,   85000, "Зарплата февраль"),
        ("income",  CAT_FREELANCE, 12000, "Проект для клиента"),
        ("expense", CAT_ZHILYO,   25000, "Аренда"),
        ("expense", CAT_EDA,      10500, "Продукты + кафе"),
        ("expense", CAT_TRANS,     3000, "Метро"),
        ("expense", CAT_HEALTH,    4200, "Врач"),
        ("expense", CAT_SUBS,      1500, "Подписки"),
        ("expense", CAT_SAVINGS,  10000, "Накопления"),
    ],
    (2024, 3): [
        ("income",  CAT_SALARY,   85000, "Зарплата март"),
        ("expense", CAT_ZHILYO,   25000, "Аренда"),
        ("expense", CAT_EDA,      11200, "Продукты"),
        ("expense", CAT_TRANS,     3500, "Транспорт"),
        ("expense", CAT_SHOP,      8900, "Одежда"),
        ("expense", CAT_SUBS,      1500, "Подписки"),
        ("expense", CAT_ENT,       3000, "Концерт"),
        ("expense", CAT_SAVINGS,  10000, "Накопления"),
    ],
    (2024, 4): [
        ("income",  CAT_SALARY,   90000, "Зарплата апрель (повышение)"),
        ("expense", CAT_ZHILYO,   25000, "Аренда"),
        ("expense", CAT_EDA,      10800, "Продукты"),
        ("expense", CAT_TRANS,     3200, "Транспорт"),
        ("expense", CAT_SUBS,      1500, "Подписки"),
        ("expense", CAT_SAVINGS,  12000, "Накопления"),
    ],
    (2024, 5): [
        ("income",  CAT_SALARY,   90000, "Зарплата май"),
        ("income",  CAT_FREELANCE, 18000, "Большой фриланс-проект"),
        ("expense", CAT_ZHILYO,   25000, "Аренда"),
        ("expense", CAT_EDA,      12000, "Продукты + рестораны"),
        ("expense", CAT_TRANS,     5500, "Поездки"),
        ("expense", CAT_ENT,       7000, "Путешествие на выходные"),
        ("expense", CAT_SUBS,      1500, "Подписки"),
        ("expense", CAT_SAVINGS,  12000, "Накопления"),
    ],
    (2024, 6): [
        ("income",  CAT_SALARY,   90000, "Зарплата июнь"),
        ("expense", CAT_ZHILYO,   25000, "Аренда"),
        ("expense", CAT_EDA,      11500, "Продукты"),
        ("expense", CAT_TRANS,     3000, "Транспорт"),
        ("expense", CAT_HEALTH,    6500, "Стоматолог"),
        ("expense", CAT_SUBS,      1500, "Подписки"),
        ("expense", CAT_SAVINGS,  12000, "Накопления"),
    ],
    (2024, 7): [
        ("income",  CAT_SALARY,   90000, "Зарплата июль"),
        ("income",  CAT_OTHER_IN,  5000, "Продал вещи"),
        ("expense", CAT_ZHILYO,   25000, "Аренда"),
        ("expense", CAT_EDA,      10200, "Продукты"),
        ("expense", CAT_TRANS,    12000, "Авиабилеты"),
        ("expense", CAT_ENT,      15000, "Отпуск"),
        ("expense", CAT_SUBS,      1500, "Подписки"),
        ("expense", CAT_SAVINGS,   5000, "Накопления (меньше из-за отпуска)"),
    ],
    (2024, 8): [
        ("income",  CAT_SALARY,   90000, "Зарплата август"),
        ("expense", CAT_ZHILYO,   25000, "Аренда"),
        ("expense", CAT_EDA,      11000, "Продукты"),
        ("expense", CAT_TRANS,     3200, "Транспорт"),
        ("expense", CAT_SHOP,      5500, "Электроника"),
        ("expense", CAT_SUBS,      1500, "Подписки"),
        ("expense", CAT_SAVINGS,  12000, "Накопления"),
    ],
    (2024, 9): [
        ("income",  CAT_SALARY,   90000, "Зарплата сентябрь"),
        ("income",  CAT_FREELANCE, 9000, "Фриланс сентябрь"),
        ("expense", CAT_ZHILYO,   25000, "Аренда"),
        ("expense", CAT_EDA,      11800, "Продукты"),
        ("expense", CAT_EDU,       8000, "Курс по Python"),
        ("expense", CAT_TRANS,     3000, "Транспорт"),
        ("expense", CAT_SUBS,      1500, "Подписки"),
        ("expense", CAT_SAVINGS,  12000, "Накопления"),
    ],
    (2024, 10): [
        ("income",  CAT_SALARY,   95000, "Зарплата октябрь (повышение)"),
        ("expense", CAT_ZHILYO,   25000, "Аренда"),
        ("expense", CAT_EDA,      12500, "Продукты"),
        ("expense", CAT_TRANS,     3500, "Транспорт"),
        ("expense", CAT_SHOP,     14000, "Зимняя куртка"),
        ("expense", CAT_SUBS,      1500, "Подписки"),
        ("expense", CAT_SAVINGS,  15000, "Накопления"),
    ],
    (2024, 11): [
        ("income",  CAT_SALARY,   95000, "Зарплата ноябрь"),
        ("income",  CAT_FREELANCE, 22000, "Крупный проект"),
        ("expense", CAT_ZHILYO,   25000, "Аренда"),
        ("expense", CAT_EDA,      13000, "Продукты + праздники"),
        ("expense", CAT_TRANS,     3200, "Транспорт"),
        ("expense", CAT_ENT,       4500, "Театр, кино"),
        ("expense", CAT_SUBS,      1500, "Подписки"),
        ("expense", CAT_SAVINGS,  15000, "Накопления"),
    ],
    (2024, 12): [
        ("income",  CAT_SALARY,   95000, "Зарплата декабрь"),
        ("income",  CAT_OTHER_IN, 10000, "Премия"),
        ("expense", CAT_ZHILYO,   25000, "Аренда"),
        ("expense", CAT_EDA,      18000, "Продукты + праздничный стол"),
        ("expense", CAT_TRANS,     4000, "Транспорт"),
        ("expense", CAT_SHOP,     20000, "Подарки"),
        ("expense", CAT_ENT,       6000, "Новогодние мероприятия"),
        ("expense", CAT_SUBS,      1500, "Подписки"),
        ("expense", CAT_SAVINGS,  10000, "Накопления"),
    ],
    # ──────────── 2025 ────────────
    (2025, 1): [
        ("income",  CAT_SALARY,  100000, "Зарплата январь"),
        ("expense", CAT_ZHILYO,   27000, "Аренда (подняли)"),
        ("expense", CAT_EDA,      13000, "Продукты"),
        ("expense", CAT_TRANS,     3500, "Транспорт"),
        ("expense", CAT_HEALTH,    3000, "Витамины"),
        ("expense", CAT_SUBS,      2000, "Подписки"),
        ("expense", CAT_SAVINGS,  18000, "Накопления"),
    ],
    (2025, 2): [
        ("income",  CAT_SALARY,  100000, "Зарплата февраль"),
        ("income",  CAT_FREELANCE, 15000, "Фриланс февраль"),
        ("expense", CAT_ZHILYO,   27000, "Аренда"),
        ("expense", CAT_EDA,      14000, "Продукты"),
        ("expense", CAT_TRANS,     3500, "Транспорт"),
        ("expense", CAT_ENT,       5000, "14 февраля"),
        ("expense", CAT_SUBS,      2000, "Подписки"),
        ("expense", CAT_SAVINGS,  18000, "Накопления"),
    ],
    (2025, 3): [
        ("income",  CAT_SALARY,  100000, "Зарплата март"),
        ("expense", CAT_ZHILYO,   27000, "Аренда"),
        ("expense", CAT_EDA,      13500, "Продукты"),
        ("expense", CAT_TRANS,     3500, "Транспорт"),
        ("expense", CAT_SHOP,      9000, "Обновил технику"),
        ("expense", CAT_EDU,      12000, "Курс по ML"),
        ("expense", CAT_SUBS,      2000, "Подписки"),
        ("expense", CAT_SAVINGS,  15000, "Накопления"),
    ],
    (2025, 4): [
        ("income",  CAT_SALARY,  100000, "Зарплата апрель"),
        ("income",  CAT_FREELANCE, 30000, "Крупный контракт"),
        ("expense", CAT_ZHILYO,   27000, "Аренда"),
        ("expense", CAT_EDA,      14500, "Продукты"),
        ("expense", CAT_TRANS,     4000, "Транспорт"),
        ("expense", CAT_ENT,       8000, "Концерт + ресторан"),
        ("expense", CAT_SUBS,      2000, "Подписки"),
        ("expense", CAT_SAVINGS,  20000, "Накопления"),
    ],
    (2025, 5): [
        ("income",  CAT_SALARY,  100000, "Зарплата май"),
        ("expense", CAT_ZHILYO,   27000, "Аренда"),
        ("expense", CAT_EDA,      14000, "Продукты"),
        ("expense", CAT_TRANS,     5000, "Транспорт"),
        ("expense", CAT_HEALTH,    8000, "Чекап"),
        ("expense", CAT_SUBS,      2000, "Подписки"),
        ("expense", CAT_SAVINGS,  20000, "Накопления"),
    ],
}


def clear_test_data():
    with get_connection() as conn:
        deleted = conn.execute(
            "DELETE FROM transactions WHERE user_id = ? AND description LIKE '%seed%' OR "
            "description IN (SELECT description FROM transactions WHERE user_id = ?)",
            (USER_ID, USER_ID)
        )
        # Проще: удаляем все транзакции пользователя кроме начального баланса
        conn.execute(
            "DELETE FROM transactions WHERE user_id = ? AND category_id != 1",
            (USER_ID,)
        )
        conn.commit()
        print("Транзакции очищены.")


def seed():
    rows = []
    for (year, month), entries in sorted(MONTHLY_DATA.items()):
        day = 5 if month % 2 == 1 else 10
        for type_, cat_id, amount, desc in entries:
            date_str = f"{year}-{month:02d}-{day:02d}"
            rows.append((USER_ID, type_, amount, cat_id, desc, date_str, 0))

    with get_connection() as conn:
        conn.executemany(
            "INSERT INTO transactions (user_id, type, amount, category_id, description, date, is_recurring) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            rows
        )
        conn.commit()
    print(f"Вставлено {len(rows)} транзакций за {len(MONTHLY_DATA)} месяцев.")


if __name__ == "__main__":
    if "--clear" in sys.argv:
        clear_test_data()
    else:
        seed()
        print("Готово. Открой аналитику и выбери год 2024 или 2025.")
