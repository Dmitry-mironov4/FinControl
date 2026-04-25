# FinControl — Обзор кодовой базы

## Структура проекта

```
FinControl/
├── fincontrolapp/                  # Flet-приложение
│   ├── main.py                     # Точка входа, навигация, авторизация, авто-операции
│   ├── database.py                 # SQLite: схема таблиц, миграции, get_connection()
│   ├── db_queries.py               # Плоский API запросов (для бота и легаси)
│   ├── calculations.py             # Чистая математика: симулятор, прогноз, savings_rate
│   ├── session.json                # Сохранённая сессия (user_id)
│   ├── database.db                 # SQLite (одна БД на проект)
│   ├── components/
│   │   ├── base_page.py            # Базовый класс экранов (Template Method)
│   │   ├── theme.py                # AppTheme: цвета, акценты
│   │   ├── dialogs.py              # show_dialog/close_dialog
│   │   ├── nav_bar.py              # build_nav() — нижняя навигация
│   │   └── form_utils.py           # Хелперы для форм
│   ├── pages/                      # UI-экраны (наследуют BasePage)
│   │   ├── auth.py                 # Авторизация / регистрация
│   │   ├── home.py                 # Главный экран
│   │   ├── transactions.py         # Все транзакции с фильтром
│   │   ├── income.py               # Доходы
│   │   ├── expenses.py             # Расходы
│   │   ├── goals.py                # Цели
│   │   ├── subscriptions.py        # Подписки
│   │   ├── analytics.py            # Аналитика (flet_charts, реальные данные)
│   │   ├── simulator.py            # Симулятор «что если»
│   │   └── settings.py             # Настройки, выход, deep link на бота
│   ├── controllers/                # Бизнес-логика для страниц
│   │   ├── home_ctrl.py
│   │   ├── transactions_ctrl.py
│   │   ├── income_ctrl.py
│   │   ├── expenses_ctrl.py
│   │   ├── goals_ctrl.py
│   │   ├── subscriptions_ctrl.py
│   │   ├── settings_ctrl.py
│   │   ├── auth_ctrl.py
│   │   └── simulator_ctrl.py
│   ├── modules/                    # Слои данных по сущностям
│   │   ├── transactions/           # model.py + repository.py + service.py
│   │   ├── goals/
│   │   ├── subscriptions/
│   │   ├── categories/
│   │   └── users/
│   └── assets/
│       ├── bg.svg                  # Фон приложения
│       ├── home/card_bg.svg
│       ├── navigation/             # Иконки нижней навигации
│       └── fonts/                  # Montserrat (Regular/Medium/SemiBold/Bold/ExtraBold)
└── bot/                            # Telegram-бот (aiogram 3, отдельный venv)
    ├── START_BOT.py                # Точка входа, регистрация роутеров, scheduler
    ├── handlers/                   # start, menu, add_dialog, quick_add, stats,
    │                               # transactions, subscriptions, goals, notify
    ├── keyboards/                  # inline.py, reply.py
    └── utils/                      # formatters, categorizer, renderers,
                                    # db_async (run_db), db_safe (@safe_db)
```

> В корне проекта дублируются `database.py` и `db_queries.py` — это **устаревшие копии** без последних миграций. Источник истины — версии внутри `fincontrolapp/`.

---

## База данных (`database.py`, `db_queries.py`, `modules/`)

### Таблицы

| Таблица | Назначение | Ключевые поля |
|---|---|---|
| `users` | Пользователи | `id`, `email`, `phone`, `telegram_id`, `password_hash` |
| `categories` | Категории дох./расх. | `id`, `name`, `type` (income/expense) |
| `transactions` | Все доходы и расходы | `user_id`, `type`, `amount`, `category_id`, `date`, `is_recurring` |
| `goals` | Финансовые цели | `user_id`, `name`, `target_amount`, `current_amount`, `deadline` |
| `subscriptions` | Подписки | `user_id`, `name`, `amount`, `charge_day`, `period`, `start_date`, `is_paused`, `last_charged_at` |

Миграции делаются через `try/except ALTER TABLE` в `create_tables()` — безопасно для уже существующих БД.

### Стартовые категории (вставляются при первом запуске)
- **Доходы:** Начальный баланс, Зарплата, Фриланс, Другое
- **Расходы:** Еда, Транспорт, Здоровье, Покупки, Развлечения, Жильё, Образование, Накопления, Другое

### Два слоя доступа

В проекте сосуществуют:

1. **`db_queries.py`** — плоский API. Используется ботом и легаси-страницами.
2. **`modules/<entity>/`** — слоистая архитектура (model + repository + service). Используется через контроллеры в новых/обновлённых страницах.

Новый код пишется через `modules/`. `db_queries.py` не расширяем (только при необходимости поддержать бот).

### Функции db_queries.py (плоский API)

```
Пользователи / привязка:
  get_user_by_telegram_id(telegram_id)       → Row | None
  get_user_by_id(user_id)                    → Row | None
  get_all_linked_users()                     → list[Row]   # для рассылок бота
  create_user(telegram_id, username, phone)  → user_id
  update_user_phone(telegram_id, phone)
  link_telegram_to_user_by_id(user_id, telegram_id) → bool

Транзакции:
  add_transaction(user_id, type_, amount, category_id, description, date, is_recurring=0)
  get_transactions(user_id, type_=None, category_id=None, limit=None) → list[Row]
  get_last_transactions(user_id, limit=10, offset=0)                  → list[Row]
  delete_transaction(transaction_id, user_id=None)
  update_transaction(transaction_id, amount, date)

Баланс / аналитика:
  get_balance(user_id)                              → float
  get_monthly_balance(user_id, year, month)         → {income, expense}
  get_monthly_data(user_id, months=6)               → помесячные суммы
  get_monthly_stats(user_id, year, month)           → dict (для бота)
  get_monthly_summary(user_id)                      → dict
  get_expense_breakdown(user_id)                    → расходы по категориям
  get_recurring_income_for_month(user_id, year, month)
  get_last_recurring_income(user_id)

Категории:
  get_categories(type_=None)  → list[Row]

Цели:
  get_goals(user_id)                                → list[Row]
  add_goal(user_id, name, target_amount, deadline)
  deposit_to_goal(user_id, goal_id, amount)         # + создаёт расход «Накопления»
  delete_goal(goal_id)

Подписки:
  get_subscriptions(user_id)                                → list[Row]
  get_subscriptions_monthly_total(user_id)                  → float (ежегодные ÷ 12)
  add_subscription(user_id, name, amount, charge_day, period='monthly', start_date=None)
  delete_subscription(subscription_id)
  get_next_charge_date(charge_day, period, start_date_str)  → date
```

### Слой modules/<entity>/

Каждая сущность — отдельный пакет:

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

Под этим паттерном живут: `transactions`, `goals`, `subscriptions`, `categories`, `users`.

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
    0: HomePage(page, HomeController(uid)),
    1: AnalyticsPage(page, uid),
    2: GoalsPage(page, GoalsController(uid)),
    3: SettingsPage(page, SettingsController(uid)),
    4: SubscriptionsPage(page, SubscriptionsController(uid)),
    5: IncomePage(page, IncomeController(uid)),
    6: ExpensesPage(page, ExpensesController(uid)),
    7: TransactionsPage(page, TransactionsController(uid)),
    8: SimulatorPage(page, SimulatorController()),
}
```

В nav bar — только индексы 0–3. Страницы 4–8 открываются программно через `page.data["navigate"](n)` из других экранов.

`navigate(index)` → `pages[index].refresh()` → меняет `content.content` → обновляет nav bar.

### Авто-операции при логине

Сразу после `on_auth_success(user_id)` (и при автологине из `session.json`) вызываются:

1. **`_check_and_add_recurring_income(user_id)`** — если за текущий месяц ещё нет recurring-зарплаты, добавляет её по шаблону последней (`get_last_recurring_income`) датой 1-го числа.
2. **`_check_and_charge_subscriptions(user_id)`** — списывает подписки с `charge_day ≤ сегодня`, у которых ещё не было списания в этом периоде.

После этого Home-страница принудительно рефрешится: `page.data["pages"][0].refresh()`.

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

### AnalyticsPage (`analytics.py`)
- Сводные плашки за выбранный год: доходы, расходы, экономия, норма сбережений
- BarChart (`flet_charts`) — доходы vs расходы по месяцам
- LineChart — накопленный баланс по месяцам
- Структура расходов по категориям (горизонтальные прогресс-бары)
- Источник данных — `get_monthly_summary`, `get_expense_breakdown_by_year`, `get_available_years` (определены в самом `analytics.py`, ходят в БД через `get_connection`)
- Заглушка, если данных меньше `MIN_MONTHS` месяцев

### SimulatorPage (`simulator.py`)
- Симулятор «что если»: покупка, новая подписка, влияние на цель, сокращение категории
- Вся математика — в `calculations.py` (чистые функции, без БД)
- Контроллер `SimulatorController()` создаётся без `user_id` — состояние ввода живёт на странице

### SettingsPage (`settings.py`)
- Изменить баланс → `page.data["show_balance_dialog"]()`
- Сбросить данные — удаляет все транзакции/цели/подписки (см. BUG-1: нет `WHERE user_id`)
- Выйти из аккаунта → `page.data["logout"]()`
- Привязать Telegram → deep link `t.me/<bot>?start=<user_id>`
- Профиль / Уведомления / Валюта — **заглушки**

---

## Telegram-бот (`bot/`)

Отдельный процесс на aiogram 3, делит БД с приложением. Запуск из корня: `cd bot && python START_BOT.py` (`START_BOT.py` сам добавляет родительскую директорию в `sys.path`).

### Хендлеры

| Файл | Что делает |
|---|---|
| `start.py` | `/start` + deep link `?start=<user_id>`, регистрация по телефону |
| `menu.py` | Callback-обработчики главного меню |
| `add_dialog.py` | FSM-диалог добавления транзакции (`/add`, `op_add_income/expense`) |
| `quick_add.py` | Быстрый ввод `+5000 зарплата` / `-300 кофе` с кнопкой «Отменить» |
| `stats.py` | `/stats` |
| `transactions.py` | История + удаление (callback `cancel_tx_<id>`) |
| `subscriptions.py` | Просмотр подписок |
| `goals.py` | Просмотр и пополнение целей |
| `notify.py` | APScheduler + рассылка напоминаний (подписки/цели/бюджет) |

> Порядок включения роутеров в `START_BOT.py` важен: `quick_add.router` идёт **до** `transactions.router` — иначе callback `cancel_tx` будет перехвачен не той веткой.

### Утилиты

| Файл | Что делает |
|---|---|
| `formatters.py` | `fmt_amount`, `format_balance`, `format_transaction`, `MONTH_SHORT` |
| `categorizer.py` | Автокатегоризация по тексту описания |
| `renderers.py` | Общие `(text, markup)` для подписок и целей; `merge_keyboards()` |
| `db_async.py` | `run_db(func, *args)` — обёртка над `asyncio.to_thread` |
| `db_safe.py` | `@safe_db()` — ловит `sqlite3.Error` / `TelegramBadRequest`, отвечает пользователю |

### Правила работы с БД из бота

- Импорт **только** `from fincontrolapp.db_queries import ...`.
- Любой синхронный вызов `db_queries.*` в async-хендлере оборачивать `await run_db(func, ...)` — иначе SQLite блокирует event loop.
- Хендлеры с БД помечать `@safe_db()`, причём декоратор должен идти **под** `@router....` (иначе роутер зарегистрирует не обёрнутую функцию).
- Не создавать `bot/database.db` — БД одна (`fincontrolapp/database.db`).

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
| Reset удаляет данные **всех** пользователей — нет `WHERE user_id` (BUG-1) | settings.py / db_queries.py | **Критично** |
| Изменение баланса дублирует транзакции (BUG-2) | диалог начального баланса | Высоко |
| Два слоя доступа к БД сосуществуют (плоский `db_queries.py` и `modules/`) | вся кодовая база | Средне — на переходный период приемлемо |
| Корневые `database.py`/`db_queries.py` отстают от `fincontrolapp/` | корень репозитория | Средне — кандидаты на удаление |
| `_show_dialog` / `_close_dialog` продублированы в pages, при том что в `components/dialogs.py` есть общие хелперы | все pages/*.py | Низко — постепенно мигрировать |
| После `self.refresh()` иногда ещё вызывается `page.update()` — двойной ре-рендер | income.py, expenses.py | Низко — избыточно, не критично |
| Колонка `field` в SQL строится через f-string в auth.py | auth.py | Низко — значение всегда "email" или "phone", контролируется кодом |
| `settings.py` — кнопки Профиль/Уведомления/Валюта не реализованы | settings.py | Средне — видно пользователю |
