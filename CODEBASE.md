# FinControl — Обзор кодовой базы

## Структура проекта

```
fincontrolapp/
├── main.py              # Точка входа, навигация, авторизация
├── database.py          # SQLite: схема таблиц, соединение
├── db_queries.py        # Все запросы к БД (функции-репозитории)
├── session.json         # Сохранённая сессия (user_id)
├── components/
│   ├── __init__.py
│   ├── base_page.py     # Базовый класс всех экранов (Template Method)
│   └── theme.py         # Цвета, стили (AppTheme)
├── pages/
│   ├── __init__.py      # Реэкспорт всех страниц
│   ├── auth.py          # Экран авторизации / регистрации
│   ├── home.py          # Главный экран (баланс, быстрые действия)
│   ├── transactions.py  # Все транзакции с фильтром
│   ├── income.py        # Доходы (зарплата + разовые)
│   ├── expenses.py      # Расходы по категориям
│   ├── goals.py         # Финансовые цели
│   ├── subscriptions.py # Подписки
│   ├── analytics.py     # Аналитика (графики — заглушка)
│   └── settings.py      # Настройки, выход
└── assets/
    ├── bg.svg           # Фон приложения
    ├── home/card_bg.svg # Фон карточки баланса
    └── navigation/      # Иконки навигации
```

---

## База данных (`database.py`, `db_queries.py`)

### Таблицы

| Таблица | Назначение | Ключевые поля |
|---|---|---|
| `users` | Пользователи | `id`, `email`, `phone`, `telegram_id`, `password_hash` |
| `categories` | Категории дох./расх. | `id`, `name`, `type` (income/expense) |
| `transactions` | Все доходы и расходы | `user_id`, `type`, `amount`, `category_id`, `date`, `is_recurring` |
| `goals` | Финансовые цели | `user_id`, `name`, `target_amount`, `current_amount`, `deadline` |
| `subscriptions` | Подписки | `user_id`, `name`, `amount`, `charge_day`, `period`, `start_date` |

### Стартовые категории (вставляются при первом запуске)
- **Доходы:** Начальный баланс, Зарплата, Фриланс, Другое
- **Расходы:** Еда, Транспорт, Здоровье, Покупки, Развлечения, Жильё, Образование, Накопления, Другое

### Функции db_queries.py

```
Транзакции:
  add_transaction(user_id, type_, amount, category_id, description, date, is_recurring)
  get_transactions(user_id, type_=None, category_id=None, limit=None)  → list[Row]
  delete_transaction(transaction_id)

Баланс:
  get_balance(user_id)          → {income, expense, balance}  # за всё время
  get_monthly_balance(user_id, year, month) → {income, expense}  # за месяц

Аналитика:
  get_monthly_data(user_id, months=6)  → помесячные суммы
  get_expense_breakdown(user_id)       → расходы по категориям

Категории:
  get_categories(type_=None)  → list[Row]

Цели:
  get_goals(user_id)          → list[Row]
  add_goal(user_id, name, target_amount, deadline)
  deposit_to_goal(user_id, goal_id, amount)  # + создаёт расход «Накопления»
  update_goal_amount(goal_id, amount)        # только обновляет, без транзакции
  delete_goal(goal_id)

Подписки:
  get_subscriptions(user_id)         → list[Row]
  get_subscriptions_monthly_total(user_id)  → float (ежегодные ÷ 12)
  add_subscription(user_id, name, amount, charge_day, period, start_date)
  delete_subscription(subscription_id)
  get_next_charge_date(charge_day, period, start_date)  → date
```

---

## Архитектура UI (`main.py`, `base_page.py`)

### Поток запуска

```
ft.run(main)
  └── create_tables()
  └── check session.json
        ├── user_id найден → show_main_app()
        └── не найден    → show_auth()
```

### Авторизация (`auth.py`)

- `AuthPage(ft.Container)` — автономный виджет, не наследует BasePage
- Два режима: `login` / `register`
- Два метода: `email` / `phone`
- Пароль хранится как `pbkdf2_hmac(sha256, password, salt, 100000)`
- При успехе вызывает `on_success(user_id, is_new=True/False)`
- `is_new=True` → показывается диалог "Начальный баланс"

### Главное приложение (функция `show_main_app` в main.py)

```
Stack
└── Image(bg.svg)          # фоновый градиент
└── Column
    ├── content (expand)   # активная страница
    └── nav_container      # нижняя навигация (80px)
```

### Навигация

```python
pages = {
    0: HomePage,
    1: TransactionsPage,
    2: GoalsPage,
    3: SettingsPage,
    4: SubscriptionsPage,  # нет кнопки в nav bar, вызывается через page.data["navigate"](4)
    5: IncomePage,         # то же
    6: ExpensesPage,       # то же
}
```

`navigate(index)` → `pages[index].refresh()` → меняет `content.content` → обновляет nav bar

### Глобальное состояние через `page.data`

| Ключ | Что хранит |
|---|---|
| `user_id` | ID текущего пользователя |
| `navigate` | функция `navigate(index)` |
| `pages` | словарь всех страниц (для cross-refresh) |
| `logout` | функция выхода из аккаунта |
| `show_balance_dialog` | показать диалог изменения начального баланса |

---

## Базовый класс страниц (`BasePage`)

```python
class BasePage(ft.Container):
    # Паттерн: Template Method
    # Структура экрана: заголовок (build_header) + тело (build_body) в ft.Column

    def __init__(self, page, title):
        ...
        self.content = ft.Column([
            self.build_header(),  # крупный заголовок
            self.build_body(),    # контент страницы
        ], scroll=AUTO)

    @property
    def _user_id(self):
        return self.page_ref.data.get("user_id")

    def refresh(self):
        # Пересобирает только build_body() (заголовок не трогает)
        self.content.controls[1] = self.build_body()
        self.page_ref.update()
```

**Важно:** дочерний `__init__` должен вызывать `super().__init__()` **последним**, иначе `build_body()` сработает до того как атрибуты класса будут готовы. Пример: `ExpensesPage.__init__` сначала устанавливает `_selected_category_id = None`, потом вызывает `super().__init__()`.

---

## Страницы — кратко

### HomePage (`home.py`)
- Баланс за всё время (`get_balance`) — основное число
- Доходы/расходы за текущий месяц (`get_monthly_balance`) — чипы под балансом
- Быстрые действия → `navigate(5/6/2/4)`
- Последние 5 операций

### ExpensesPage (`expenses.py`)
- Сетка категорий (4 колонки) — клик фильтрует список
- Список расходов с удалением (с подтверждением)
- После добавления: `self.refresh()` + `pages[0].refresh()` + snackbar

### IncomePage (`income.py`)
- Карточка зарплаты (`is_recurring=1`) — редактируемая
- Список разовых доходов
- После добавления: аналогично expenses

### GoalsPage (`goals.py`)
- Карточка цели: прогресс-бар, процент, темп накоплений
- `_calc_pace(target, current, deadline)` → строка "Нужно: X ₽/мес · осталось N мес."
- Пополнение через `deposit_to_goal` — деньги списываются с баланса как расход "Накопления"
- 100% → зелёный цвет, иконка трофея, "Цель достигнута!"

### SubscriptionsPage (`subscriptions.py`)
- Суммарная стоимость в месяц (ежегодные ÷ 12)
- `get_next_charge_date(charge_day, period, start_date)` — вычисляет следующее списание
- В карточке: "Следующее: 1 апр."

### TransactionsPage (`transactions.py`)
- Все транзакции, фильтр: Все / Доходы / Расходы
- Добавление (категория + сумма + дата + описание), удаление

### SettingsPage (`settings.py`)
- Профиль, Уведомления, Валюта, Telegram-бот — **заглушки** (нет логики)
- Изменить баланс → `page.data["show_balance_dialog"]()`
- Сбросить данные — удаляет все транзакции/цели/подписки
- Выйти из аккаунта → `page.data["logout"]()`

---

## Оценка качества кода

### Хорошо ✓
- Чёткое разделение слоёв: схема → запросы → UI
- BasePage устраняет дублирование структуры экранов
- `page.data` как лёгкий DI-контейнер — понятно и прагматично
- Все запросы в db_queries.py — UI не знает про SQL
- SQLite Row Factory — доступ по имени (`row['amount']`) вместо индексов
- Миграции через `try/except ALTER TABLE` — не ломает существующую БД

### Есть нюансы ⚠
| Проблема | Где | Насколько критично |
|---|---|---|
| `_show_dialog` / `_close_dialog` продублированы в каждом файле | все pages/*.py | Низко — работает, просто повтор |
| `update_goal_amount` больше не используется (заменена `deposit_to_goal`) | db_queries.py | Низко — мёртвый код |
| После `self.refresh()` иногда ещё вызывается `page.update()` — двойной ре-рендер | income.py, expenses.py | Низко — избыточно, не критично |
| Колонка `field` в SQL строится через f-string в auth.py | auth.py:181 | Низко — значение всегда "email" или "phone", контролируется кодом |
| `settings.py` — кнопки Профиль/Уведомления/Валюта/Telegram не реализованы | settings.py | Средне — видно пользователю |
