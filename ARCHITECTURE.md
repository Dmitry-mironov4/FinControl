# FinControl — Архитектура

## 1. Общий поток данных

```
Пользователь
    │
    ▼
ft.Page (Flet runtime)
    │
    ├── page.data (глобальное состояние)
    │       ├── user_id: int
    │       ├── navigate: func(index)
    │       ├── pages: dict[int, BasePage]
    │       ├── logout: func()
    │       └── show_balance_dialog: func()
    │
    ├── Stack
    │     ├── Image(bg.svg)         ← фон
    │     └── inner (Container)     ← меняется между AuthPage и основным приложением
    │
    └── Диалоги (через page.show_dialog / page.pop_dialog)
```

### Жизненный цикл запроса пользователя

```
Нажатие кнопки "Добавить расход"
    │
    ▼
ExpensesPage._open_add_dialog()     ← создаёт AlertDialog
    │
    ▼
page.show_dialog(dlg)               ← Flet показывает диалог поверх всего
    │
on_submit()
    │
    ├── add_transaction(...)         ← INSERT в SQLite
    ├── self.refresh()               ← пересобирает build_body() текущей страницы
    ├── pages[0].refresh()           ← синхронизирует HomePage (баланс)
    ├── page.snack_bar = ...         ← уведомление внизу
    └── page.pop_dialog()            ← закрывает диалог
```

---

## 2. BasePage — Template Method

```python
BasePage(ft.Container)
    │
    ├── __init__(page, title)
    │     └── self.content = ft.Column([
    │               build_header(),   ← заголовок страницы (переопределяемый)
    │               build_body(),     ← АБСТРАКТНЫЙ, каждая страница реализует сама
    │         ], scroll=AUTO)
    │
    ├── build_header() → ft.Text(title, size=45, bold)
    ├── build_body()   → ft.Container()  ← заглушка
    ├── _user_id       → page.data["user_id"]
    └── refresh()      → content.controls[1] = build_body(); page.update()
```

**Важный порядок инициализации:**
```python
class ExpensesPage(BasePage):
    def __init__(self, page, ctrl):
        self._selected_category_id = None   # ← СНАЧАЛА атрибуты
        super().__init__(page, "Расходы")   # ← ПОТОМ super() — вызовет build_body()
```
Если поставить `super()` первым — `build_body()` сработает раньше, чем `_selected_category_id` создан → `AttributeError`.

---

## 3. Слой данных

В проекте сосуществуют **два** слоя доступа к БД:

### 3.1 Плоский API — `fincontrolapp/db_queries.py`

Простой набор функций (`get_balance`, `get_transactions`, `add_transaction`, …). Используется:
- **Telegram-ботом** — единственный разрешённый интерфейс к БД из `bot/`.
- Старыми страницами/диалогами (легаси).

Не расширять. Новый код пишется через слоистую архитектуру (см. 3.2).

### 3.2 Слоистая архитектура — `modules/<entity>/`

```
modules/
└── <entity>/
    ├── model.py       # @dataclass — структура сущности
    ├── repository.py  # SQL-запросы, на вход sqlite3.Connection
    └── service.py     # бизнес-логика поверх репозитория
```

Поток вызовов:
```
Page (UI)
  └── Controller (controllers/<name>_ctrl.py)
        └── Service.method()
              └── Repository.method()
                    └── sqlite3 (через get_connection())
```

Контроллер инжектируется в страницу:
```python
HomePage(page, HomeController(uid))
```
и оборачивает работу с соединением:
```python
def get_balance(self) -> dict:
    with get_connection() as con:
        row = TransactionRepository(con).get_balance(self._user_id)
    ...
```

Сейчас по этому паттерну живут: `transactions`, `goals`, `subscriptions`, `categories`, `users`, `budgets`.

### Соединение с БД

```python
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # доступ row['field'] вместо row[0]
    return conn
```

`sqlite3.Connection` поддерживает context manager (`with get_connection() as conn`), но он только делает `commit()` / `rollback()` — **соединение не закрывает**. Для SQLite на десктопе это нормально.

### Как устроена функция с фильтрами (репозиторий)

```python
def get_transactions(self, user_id, type_=None, category_id=None, limit=None):
    query = "SELECT ... WHERE user_id = ?"
    params = [user_id]
    if type_:
        query += " AND t.type = ?"
        params.append(type_)
    return self.con.execute(query, tuple(params)).fetchall()
```

Параметры передаются через `?` — защита от SQL-инъекций.

---

## 4. Навигация (main.py)

### Ленивое создание страниц

Страницы создаются **по первому обращению** через словарь фабрик, а не все сразу при старте:

```python
_factories = {
    1: lambda: AnalyticsPage(page, uid, budget_controller=BudgetController(uid)),
    2: lambda: GoalsPage(page, GoalsController(uid)),
    3: lambda: SettingsPage(page, SettingsController(uid)),
    4: lambda: SubscriptionsPage(page, SubscriptionsController(uid)),
    5: lambda: IncomePage(page, IncomeController(uid)),
    6: lambda: ExpensesPage(page, ExpensesController(uid)),
    7: lambda: TransactionsPage(page, TransactionsController(uid)),
    8: lambda: SimulatorPage(page, SimulatorController()),
    9: lambda: BudgetPage(page, BudgetController(uid)),
}
pages = {0: HomePage(page, HomeController(uid))}  # HomePage создаётся сразу

def _get_page(index: int):
    if index not in pages:
        pages[index] = _factories[index]()
    return pages[index]
```

### AnimatedSwitcher (реализован)

Переходы между страницами — через `ft.AnimatedSwitcher` с fade-анимацией (duration=150ms):

```python
content = ft.AnimatedSwitcher(
    content=ft.Container(content=_get_page(0), key="0"),
    expand=True,
    transition=ft.AnimatedSwitcherTransition.FADE,
    duration=150,
)
```

### Функция navigate

```python
def navigate(index: int):
    pg = _get_page(index)
    pg.key = str(index) + "_" + str(id(pg))  # уникальный ключ для AnimatedSwitcher
    content.content = pg
    nav_container.content = build_nav(index)
    page.update()
```

Страницы в nav bar — только индексы 0, 1, 2, 8, 3. Страницы 4–7, 9 открываются программно через `page.data["navigate"](n)` из других экранов.

**Кросс-обновление:** после изменения данных вызывается `page.data["pages"][0].refresh()`, чтобы HomePage синхронизировалась.

---

## 5. Авторизация (auth.py)

```
AuthPage (ft.Container)
    │
    ├── _mode: 'login' | 'register'
    ├── _method: 'email' | 'phone'
    │
    ├── _build()        ← полностью пересобирает UI при смене режима
    ├── _rebuild()      ← сбрасывает ошибку + вызывает _build()
    │
    ├── _register(contact, password)
    │     ├── pbkdf2_hmac(sha256, password, random_salt, 100_000_iterations)
    │     ├── INSERT INTO users
    │     └── on_success(user_id, is_new=True)
    │
    └── _login(contact, password)
          ├── SELECT ... WHERE email/phone = ?
          ├── verify_password(stored_hash, provided)
          └── on_success(user_id, is_new=False)
```

Хеш пароля хранится как `"salt_hex:key_hex"` — 16-байтовая соль + 32-байтовый ключ.

---

## 6. Цели — логика достижения

```python
def deposit_to_goal(user_id, goal_id, amount):
    UPDATE goals SET current_amount = current_amount + amount
    INSERT INTO transactions (type='expense', category='Накопления', amount)
```

Пополнение цели — это расход. Деньги реально уходят с баланса.

```python
def _calc_pace(target, current, deadline):
    remaining = target - current
    days_left = (deadline - today).days
    per_month = remaining / (days_left / 30)
    return f"Нужно: {per_month:,.0f} ₽/мес · осталось {months} мес."
```

---

## 7. Подписки — вычисление следующего списания

```python
def get_next_charge_date(charge_day, period, start_date):
    # ежемесячные: ближайший charge_day в текущем или следующем месяце
    # ежегодные:   ближайшая годовщина от start_date
```

Суммарная стоимость подписок в месяц:
```sql
SUM(CASE WHEN period='monthly' THEN amount
         WHEN period='yearly'  THEN amount / 12.0
    END)
```

---

## 8. Главный экран — два вида баланса

```
Основное число  = get_balance()         → всё время (реальные деньги на счёте)
Чипы доходов    = get_monthly_balance() → только текущий месяц
Чипы расходов   = get_monthly_balance() → только текущий месяц
```

Логика: баланс показывает сколько у тебя есть, чипы — как ты тратишь сейчас.

---

## 9. Симулятор «что если» (`pages/simulator.py`, `calculations.py`)

Страница (индекс 8), четыре вкладки:
- покупка сейчас при зарплате через N дней;
- влияние новой подписки на свободный остаток;
- как покупка сдвинет дедлайн цели;
- эффект сокращения категории расходов на накопления.

Вся математика — в `calculations.py`, чистые функции **без обращения к БД**:
- `savings_rate(income, expense)` — норма сбережений в %.
- `moving_average(values, n)` — скользящее среднее.
- `linear_forecast(values, steps)` — линейная экстраполяция (МНК).
- `goal_analysis(target, current, monthly_savings)` — сколько месяцев до цели.
- `subscription_load(subs_total, income)` — доля подписок в доходе.
- `sim_purchase`, `sim_goal_impact`, `sim_new_subscription`, `sim_cut_category` — сценарные расчёты.

`SimulatorController()` создаётся **без user_id** — состояние ввода живёт на странице.

**Ограничение:** не подключать ML-библиотеки (scikit-learn / statsmodels / scipy) — они несовместимы с мобильной сборкой Flet.

---

## 10. Telegram-бот (`bot/`)

Запускается отдельным процессом, делит БД с приложением.

```
START_BOT.py
  ├── load_dotenv() → BOT_TOKEN
  ├── Bot, Dispatcher
  ├── include_router(start, add_dialog, goals, quick_add, transactions, stats, subscriptions, menu)
  │     # quick_add ДО transactions — иначе callback cancel_tx уйдёт не в ту ветку
  └── main():
        scheduler = setup_notify_scheduler(bot)   # APScheduler из handlers/notify.py
        scheduler.start()
        await dp.start_polling(bot)
```

### Слой БД для бота

Прямой `sqlite3.connect` блокирует aiogram event loop. Поэтому:

```python
from bot.utils.db_async import run_db
from fincontrolapp.db_queries import get_balance

balance = await run_db(get_balance, user["id"])   # asyncio.to_thread под капотом
```

Декоратор для отказоустойчивости:

```python
@router.message(Command("stats"))
@safe_db()                      # ловит sqlite3.Error и TelegramBadRequest
async def cmd_stats(message): ...
```

Порядок декораторов: `@router....` выше, `@safe_db()` ниже — иначе роутер зарегистрирует не обёрнутую функцию.

### Quick-add и категоризация

`handlers/quick_add.py` парсит сообщения вида `+5000 зарплата` / `-300.50 кофе`:
```python
_PATTERN = re.compile(r'^([+-])(\d+(?:[.,]\d+)?)\s+(.+)$', re.DOTALL)
```
Категория угадывается через `bot/utils/categorizer.py`; пользователь видит inline-кнопку «Отменить» (`cancel_tx_<id>`).

### Уведомления (`handlers/notify.py`)

APScheduler с CronTrigger:
- ежедневно — напоминание о подписках, которые спишутся завтра;
- по понедельникам — сводка по целям и бюджету.

Адресаты — `get_all_linked_users()` (только привязанные через deep link).

---

## 11. Реализованные Flet-паттерны

### 11.1 DatePicker для выбора дат — ✅ внедрено

В формах добавления транзакций, доходов и подписок используется `ft.DatePicker` вместо текстового поля.
Файлы: `pages/expenses.py`, `pages/income.py`, `pages/transactions.py`, `pages/subscriptions.py`.

```python
date_picker = ft.DatePicker(
    first_date=date(2020, 1, 1),
    last_date=date(2030, 12, 31),
    on_change=lambda e: ...,
)
```

### 11.2 BottomSheet для форм — ✅ внедрено

Формы добавления выезжают снизу через `ft.BottomSheet` (нативнее для мобильного UI, чем `AlertDialog`).
Используется во всех страницах с CRUD: `expenses`, `income`, `subscriptions`, `transactions`.

```python
bs = ft.BottomSheet(open=False, content=ft.Container())
page.open(bs)
```

### 11.3 Dismissible для свайпа удаления — ✅ внедрено

В `home.py` последние транзакции удаляются свайпом влево через `ft.Dismissible`.

```python
ft.Dismissible(
    content=transaction_row,
    direction=ft.DismissDirection.END_TO_START,
    on_dismiss=lambda e: delete_transaction(t['id']),
    dismiss_thresholds={ft.DismissDirection.END_TO_START: 0.3},
)
```

### 11.4 AnimatedSwitcher для переходов — ✅ внедрено

Fade-анимация (150ms) между экранами — см. раздел 4.

---

## 12. Возможные улучшения

### 12.1 SegmentedButton для фильтра транзакций

Сейчас в `TransactionsPage` фильтр Все / Доходы / Расходы — три кнопки. `SegmentedButton` дал бы более нативный вид:

```python
ft.SegmentedButton(
    selected={"all"},
    segments=[
        ft.Segment(value="all",     label=ft.Text("Все")),
        ft.Segment(value="income",  label=ft.Text("Доходы")),
        ft.Segment(value="expense", label=ft.Text("Расходы")),
    ],
    on_change=lambda e: self._set_filter(e.control.selected.pop()),
)
```

### 12.2 Реактивное состояние вместо ручного refresh()

Сейчас после каждого изменения нужно явно вызывать `self.refresh()` + `pages[0].refresh()` + `page.update()`.
Паттерн Observer решил бы это:

```python
class AppStore:
    _listeners: list[callable] = []

    def on_change(self, fn):
        self._listeners.append(fn)

    def notify(self):
        for fn in self._listeners:
            fn()
```

Flet не имеет встроенного state management, поэтому пришлось бы реализовать самостоятельно.

---

## 13. Состояние задач

| Функция | Сложность | Статус |
|---|---|---|
| Мультивалютность | Высокая | ✅ сделано |
| Telegram-бот интеграция | Высокая | ✅ сделано |
| Уведомления (бот) | Высокая | ✅ сделано |
| Аналитика с графиками | Средняя | ✅ сделано |
| Бюджеты по категориям | Средняя | ✅ сделано |
| Симулятор «что если» | Средняя | ✅ сделано |
| DatePicker в диалогах | Низкая | ✅ сделано |
| BottomSheet для форм | Низкая | ✅ сделано |
| Swipe to delete | Низкая | ✅ сделано |
| AnimatedSwitcher переходы | Низкая | ✅ сделано |
| SegmentedButton для фильтра | Низкая | TODO |
| Экспорт данных (CSV/PDF) | Средняя | TODO |
| Тёмная тема | Низкая | TODO |

