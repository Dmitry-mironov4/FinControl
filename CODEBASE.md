# FinControl — Обзор кодовой базы

## Структура проекта

```
FinControl/
├── fincontrolapp/                  # Flet-приложение
│   ├── main.py                     # Точка входа, навигация, авторизация, авто-операции
│   ├── database.py                 # SQLite: схема таблиц, миграции, get_connection()
│   ├── db_queries.py               # Плоский API запросов (для бота и легаси)
│   ├── calculations.py             # Чистая математика: симулятор, прогноз, savings_rate
│   ├── utils.py                    # get_currency_symbol и прочие утилиты
│   ├── components/
│   │   ├── base_page.py            # Базовый класс экранов (Template Method)
│   │   ├── theme.py                # AppTheme: цвета, акценты
│   │   ├── dialogs.py              # show_dialog/close_dialog
│   │   ├── nav_bar.py              # build_nav() — нижняя навигация
│   │   ├── empty_state.py          # Виджет-заглушка «нет данных»
│   │   └── form_utils.py           # Хелперы для форм
│   ├── pages/                      # UI-экраны (наследуют BasePage)
│   │   ├── auth.py                 # Авторизация / регистрация
│   │   ├── home.py                 # Главный экран (баланс, быстрые действия, история)
│   │   ├── transactions.py         # Все транзакции с фильтром
│   │   ├── income.py               # Доходы
│   │   ├── expenses.py             # Расходы
│   │   ├── goals.py                # Цели
│   │   ├── subscriptions.py        # Подписки
│   │   ├── analytics.py            # Аналитика (flet_charts, графики, бюджеты)
│   │   ├── budget.py               # Управление бюджетами (открывается из аналитики)
│   │   ├── simulator.py            # Симулятор «что если»
│   │   └── settings.py             # Настройки, выход, deep link на бота
│   ├── controllers/                # Бизнес-логика для страниц
│   │   ├── home_ctrl.py
│   │   ├── transactions_ctrl.py
│   │   ├── income_ctrl.py
│   │   ├── expenses_ctrl.py
│   │   ├── goals_ctrl.py
│   │   ├── subscriptions_ctrl.py
│   │   ├── budget_ctrl.py
│   │   ├── settings_ctrl.py
│   │   ├── auth_ctrl.py
│   │   └── simulator_ctrl.py
│   ├── modules/                    # Слои данных по сущностям
│   │   ├── transactions/           # model.py + repository.py + service.py
│   │   ├── goals/
│   │   ├── subscriptions/
│   │   ├── categories/
│   │   ├── budgets/
│   │   └── users/
│   └── assets/
│       ├── bg.svg                  # Фон приложения
│       ├── home/card_bg.svg
│       ├── navigation/             # Иконки нижней навигации (SVG)
│       └── fonts/                  # Montserrat (Regular/Medium/SemiBold/Bold/ExtraBold)
└── bot/                            # Telegram-бот (aiogram 3, отдельный venv)
    ├── START_BOT.py                # Точка входа, регистрация роутеров, scheduler
    ├── handlers/                   # start, menu, add_dialog, quick_add, stats,
    │                               # transactions, subscriptions, goals, notify
    ├── keyboards/                  # inline.py, reply.py
    └── utils/                      # formatters, categorizer, renderers,
                                    # db_async (run_db), db_safe (@safe_db)
```

> В корне проекта дублируются `database.py` и `db_queries.py` — устаревшие копии без последних миграций. Источник истины — версии внутри `fincontrolapp/`.

---

## База данных (`database.py`, `db_queries.py`, `modules/`)

### Таблицы

| Таблица | Назначение | Ключевые поля |
|---|---|---|
| `users` | Пользователи | `id`, `email`, `phone`, `telegram_id`, `password_hash` |
| `categories` | Категории дох./расх. | `id`, `name`, `type` (income/expense) |
| `transactions` | Все доходы и расходы | `user_id`, `type`, `amount`, `category_id`, `date`, `is_recurring` |
| `goals` | Финансовые цели | `user_id`, `name`, `target_amount`, `current_amount`, `deadline` |
| `subscriptions` | Подписки | `user_id`, `name`, `amount`, `charge_day`, `period`, `is_paused`, `last_charged_at` |
| `budgets` | Лимиты по категориям | `user_id`, `category_id`, `limit_amount`, `period` |
| `purchase_timers` | Таймеры обдумывания покупок | `user_id`, `item_name`, `amount`, `remind_at`, `decision` |

Миграции — через `try/except ALTER TABLE` в `create_tables()`.

### Стартовые категории (вставляются при первом запуске)
- **Доходы:** Начальный баланс, Зарплата, Фриланс, Другое
- **Расходы:** Еда, Транспорт, Здоровье, Покупки, Развлечения, Жильё, Образование, Накопления, Другое, Подписки

### Два слоя доступа

1. **`db_queries.py`** — плоский API. Используется ботом и легаси-страницами.
2. **`modules/<entity>/`** — слоистая архитектура (model + repository + service). Используется через контроллеры.

Новый код пишется через `modules/`. `db_queries.py` не расширяется (только при поддержке бота).

### Функции db_queries.py (плоский API)

```
Пользователи / привязка:
  get_user_by_telegram_id(telegram_id)
  get_user_by_id(user_id)
  get_all_linked_users()                     # для рассылок бота
  link_telegram_to_user_by_id(user_id, telegram_id) → bool

Транзакции:
  add_transaction(user_id, type_, amount, category_id, description, date, is_recurring=0)
  get_transactions(user_id, type_=None, category_id=None, limit=None)
  get_last_transactions(user_id, limit=10, offset=0)
  delete_transaction(transaction_id, user_id=None)
  update_transaction(transaction_id, amount, date)

Баланс / аналитика:
  get_balance(user_id)
  get_monthly_balance(user_id, year, month)  → {income, expense}
  get_monthly_data(user_id, months=6)
  get_monthly_stats(user_id, year, month)    → dict (для бота)
  get_monthly_summary(user_id)
  get_expense_breakdown(user_id)
  get_recurring_income_for_month(user_id, year, month)
  get_last_recurring_income(user_id)

Категории:
  get_categories(type_=None)

Цели:
  get_goals(user_id)
  add_goal(user_id, name, target_amount, deadline)
  deposit_to_goal(user_id, goal_id, amount)  # + создаёт расход «Накопления»
  delete_goal(goal_id)

Подписки:
  get_subscriptions(user_id)
  get_subscriptions_monthly_total(user_id)   # ежегодные ÷ 12
  add_subscription(user_id, name, amount, charge_day, period='monthly', start_date=None)
  delete_subscription(subscription_id)
  get_next_charge_date(charge_day, period, start_date_str)
```

### Слой modules/<entity>/

```
modules/transactions/
├── model.py        # @dataclass Transaction
├── repository.py   # class TransactionRepository(con: sqlite3.Connection)
└── service.py      # class TransactionService(repository)
```

Контроллеры открывают соединение и пробрасывают его в репозиторий:

```python
class HomeController:
    def get_balance(self) -> dict:
        with get_connection() as con:
            row = TransactionRepository(con).get_balance(self._user_id)
        ...
```

---

## Архитектура UI (`main.py`, `base_page.py`)

### Поток запуска

```
ft.run(main)
  └── create_tables()
  └── check session.json
        ├── user_id найден → show_main_app() → AUTO-1 + AUTO-2
        └── не найден    → show_auth()
```

### Авторизация (`auth.py`)

- `AuthPage(ft.Container)` — автономный виджет, не наследует `BasePage`
- Два режима: `login` / `register`; два метода: `email` / `phone`
- Пароль: `pbkdf2_hmac(sha256, password, salt, 100000)`, хранится как `"salt_hex:key_hex"`
- При успехе вызывает `on_success(user_id, is_new=True/False)`

### Главное приложение (`show_main_app` в main.py)

```
Stack
└── Image(bg.svg)          # фоновый градиент
└── Column
    ├── AnimatedSwitcher   # активная страница (fade, 150ms)
    └── nav_container      # нижняя навигация (80px)
```

### Навигация

| Индекс | Страница | В nav bar | Откуда открывается |
|---|---|---|---|
| 0 | HomePage | ✅ home | — |
| 1 | AnalyticsPage | ✅ analytics | — |
| 2 | GoalsPage | ✅ goals | — |
| 3 | SettingsPage | ✅ settings | — |
| 4 | SubscriptionsPage | — | HomePage |
| 5 | IncomePage | — | HomePage |
| 6 | ExpensesPage | — | HomePage |
| 7 | TransactionsPage | — | HomePage |
| 8 | SimulatorPage | ✅ test | — |
| 9 | BudgetPage | — | AnalyticsPage |

Страницы создаются **лениво** (при первом обращении через `_factories`). `pages[0]` (HomePage) создаётся сразу.

### Авто-операции при логине

После `on_auth_success(user_id)` (и при автологине):

1. **AUTO-1** `_check_and_add_recurring_income(user_id)` — добавляет зарплату 1-го числа, если за текущий месяц ещё нет recurring-зарплаты.
2. **AUTO-2** `_check_and_charge_subscriptions(user_id)` — списывает подписки с `charge_day ≤ сегодня`, которые ещё не списывались в этом периоде.

После — принудительный `pages[0].refresh()`.

### Глобальное состояние через `page.data`

| Ключ | Что хранит |
|---|---|
| `user_id` | ID текущего пользователя |
| `navigate` | функция `navigate(index)` |
| `pages` | словарь всех инициализированных страниц |
| `logout` | функция выхода |
| `show_balance_dialog` | показать диалог изменения начального баланса |
| `_s_currency` | символ валюты (по умолчанию `"RUB"`) |

---

## Базовый класс страниц (`BasePage`)

```python
class BasePage(ft.Container):
    def __init__(self, page, title):
        self.content = ft.Column([
            self.build_header(),  # крупный заголовок
            self.build_body(),    # контент страницы
        ], scroll=AUTO)

    @property
    def _user_id(self):
        return self.page_ref.data.get("user_id")

    def refresh(self):
        self.content.controls[1] = self.build_body()
        self.page_ref.update()
```

**Важно:** дочерний `__init__` вызывает `super().__init__()` **последним** — иначе `build_body()` сработает до того, как атрибуты класса будут готовы.

---

## Страницы — кратко

### HomePage (`home.py`)
- Баланс за всё время (`get_balance`) — основное число
- Доходы/расходы за текущий месяц (`get_monthly_balance`) — чипы под балансом
- Быстрые действия → `navigate(5/6/2/4)`
- Последние 5 операций

### ExpensesPage (`expenses.py`)
- Сетка категорий (4 колонки) — клик фильтрует список
- После добавления: `self.refresh()` + `pages[0].refresh()` + snackbar

### IncomePage (`income.py`)
- Карточка зарплаты (`is_recurring=1`) — редактируемая
- Список разовых доходов

### GoalsPage (`goals.py`)
- Прогресс-бар, процент, темп накоплений (`_calc_pace`)
- Пополнение через `deposit_to_goal` — деньги списываются как расход "Накопления"
- 100% → зелёный цвет, иконка трофея

### SubscriptionsPage (`subscriptions.py`)
- Суммарная стоимость в месяц (ежегодные ÷ 12)
- `get_next_charge_date` — вычисляет следующее списание
- Пауза/возобновление подписки

### TransactionsPage (`transactions.py`)
- Все транзакции, фильтр: Все / Доходы / Расходы
- Добавление и удаление

### AnalyticsPage (`analytics.py`)
- Сводные плашки за выбранный год: доходы, расходы, экономия, норма сбережений
- `BarChart` — доходы vs расходы по месяцам
- `LineChart` — накопленный баланс по месяцам
- Структура расходов по категориям
- Бюджеты — прогресс-бары по категориям; кнопка → `navigate(9)`
- Заглушка если меньше `MIN_MONTHS` месяцев данных

### BudgetPage (`budget.py`)
- Создание и удаление лимитов по категориям
- Период: `monthly` / `yearly`
- Открывается из AnalyticsPage через `navigate(9)`

### SimulatorPage (`simulator.py`)
- 4 вкладки «что если»
- Математика в `calculations.py` (чистые функции)
- `SimulatorController()` без `user_id`

### SettingsPage (`settings.py`)
- Изменить баланс → `page.data["show_balance_dialog"]()`
- Сбросить данные (⚠ нет `WHERE user_id` — BUG-1)
- Выйти → `page.data["logout"]()`
- Привязать Telegram → deep link `t.me/<bot>?start=<user_id>`
- Профиль / Уведомления / Валюта — **заглушки**

---

## Telegram-бот (`bot/`)

Отдельный процесс на aiogram 3. Запуск: `cd bot && python START_BOT.py`.

### Хендлеры

| Файл | Что делает |
|---|---|
| `start.py` | `/start` + deep link `?start=<user_id>`, регистрация |
| `menu.py` | Callback-обработчики главного меню |
| `add_dialog.py` | FSM-диалог добавления транзакции |
| `quick_add.py` | Быстрый ввод `+5000 зарплата` / `-300 кофе` с кнопкой «Отменить» |
| `stats.py` | `/stats` |
| `transactions.py` | История + удаление |
| `subscriptions.py` | Просмотр подписок |
| `goals.py` | Просмотр и пополнение целей |
| `notify.py` | APScheduler + рассылка напоминаний |

> Порядок роутеров в `START_BOT.py` важен: `quick_add.router` идёт **до** `transactions.router`.

### Утилиты

| Файл | Что делает |
|---|---|
| `formatters.py` | `fmt_amount`, `format_balance`, `format_transaction`, `MONTH_SHORT` |
| `categorizer.py` | Автокатегоризация текста → категория |
| `renderers.py` | Общие `(text, markup)` для подписок/целей; `merge_keyboards()` |
| `db_async.py` | `run_db(func, *args)` — `asyncio.to_thread` для SQLite |
| `db_safe.py` | `@safe_db()` — ловит `sqlite3.Error` / `TelegramBadRequest` |

### Правила работы с БД из бота

- Импорт **только** `from fincontrolapp.db_queries import ...`
- Синхронный вызов в async-хендлере: `await run_db(func, ...)`
- Хендлеры с БД: `@safe_db()` под `@router....`
- Не создавать отдельную `bot/database.db`


