# FinControl — Подробная архитектура и альтернативы

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
    ├── pages[0].refresh()           ← пересобирает build_body() HomePage
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
    def __init__(self, page):
        self._selected_category_id = None   # ← СНАЧАЛА атрибуты
        super().__init__(page, "Расходы")   # ← ПОТОМ super() — вызовет build_body()
```
Если поставить super() первым — `build_body()` вызовется раньше, чем `_selected_category_id` создан → AttributeError.

---

## 3. Слой данных

В проекте сосуществуют **два** слоя доступа к БД:

### 3.1 Плоский API — `fincontrolapp/db_queries.py`

Простой набор функций (`get_balance`, `get_transactions`, `add_transaction`, …). Используется:
- **Telegram-ботом** — это единственный разрешённый интерфейс к БД из `bot/`.
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

Сейчас по этому паттерну живут: `transactions`, `goals`, `subscriptions`, `categories`, `users`.

### Соединение с БД

```python
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # доступ row['field'] вместо row[0]
    return conn
```

`sqlite3.Connection` поддерживает context manager (`with get_connection() as conn`),
но он только делает `commit()` / `rollback()` — **соединение не закрывает**.
Соединение закрывается сборщиком мусора. Для SQLite на десктопе это нормально.

### Как устроена функция с фильтрами (репозиторий)

```python
def get_transactions(self, user_id, type_=None, category_id=None, limit=None):
    query = "SELECT ... WHERE user_id = ?"
    params = [user_id]
    if type_:
        query += " AND t.type = ?"
        params.append(type_)
    # ... динамически добиваем условия
    return self.con.execute(query, tuple(params)).fetchall()
```

Параметры передаются через `?` (параметризованный запрос) — защита от SQL-инъекций.

---

## 4. Навигация (main.py)

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

def navigate(index):
    pages[index].refresh()        # пересобирает данные
    content.content = pages[index] # показывает страницу
    nav_container.content = build_nav(index)  # подсвечивает кнопку
    content.update()
    nav_container.update()
```

Страницы создаются **один раз** при запуске и переиспользуются.
`refresh()` пересобирает только `build_body()`, не весь виджет.

**Страницы 4, 5, 6, 7, 8** (Подписки, Доходы, Расходы, Транзакции, Симулятор) не имеют кнопок в nav bar — они открываются только через `page.data["navigate"](n)` из других экранов.

**Кросс-обновление страниц:** после изменения данных вызывается `page.data["pages"][0].refresh()`, чтобы Home-экран синхронизировался (баланс, последние операции).

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

Хеш пароля хранится как `"salt_hex:key_hex"`:
```
"a1b2c3...:d4e5f6..."   ← 16-байтовая соль + 32-байтовый ключ
```

---

## 6. Цели — логика достижения

```python
def deposit_to_goal(user_id, goal_id, amount):
    UPDATE goals SET current_amount = current_amount + amount
    INSERT INTO transactions (type='expense', category='Накопления', amount)
```

Пополнение цели — это расход. Деньги реально уходят с баланса.
Прогресс = `current_amount / target_amount`, показывается как прогресс-бар.

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

Отдельная страница (индекс 8), отвечает на сценарии вида:
- покупка сейчас при зарплате через N дней;
- влияние новой подписки на свободный остаток;
- как покупка сдвинет дедлайн цели;
- эффект сокращения категории расходов на накопления.

Вся математика — в `calculations.py`, чистые функции **без обращения к БД**:
- `savings_rate(income, expense)` — норма сбережений в %.
- `moving_average(values, n)` — скользящее среднее.
- `linear_forecast(values, steps)` — линейная экстраполяция (МНК) на `steps` шагов вперёд.
- `goal_analysis(target, current, monthly_savings)` — сколько месяцев до цели.
- `subscription_load(subs_total, income)` — доля подписок в доходе.
- `sim_purchase`, `sim_goal_impact`, `sim_new_subscription`, `sim_cut_category` — сценарные расчёты, возвращают dict с показателями для UI.

Контроллер `SimulatorController()` создаётся **без user_id** — состояние ввода живёт на странице, цифры берутся из репозиториев по запросу.

**Важно:** не подключать ML-библиотеки (scikit-learn / statsmodels / scipy) — они несовместимы с мобильной сборкой Flet. Прогноз делается вручную через МНК в `linear_forecast`.

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

И декоратор для отказоустойчивости:

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
Категория угадывается через `bot/utils/categorizer.py`; пользователь видит inline-кнопку «Отменить» (`cancel_tx_<id>`), которая удаляет транзакцию через `delete_transaction`.

### Уведомления (`handlers/notify.py`)

APScheduler с CronTrigger:
- ежедневно — напоминание о подписках, которые спишутся завтра;
- по понедельникам — сводка по целям и бюджету.

Адресаты — `get_all_linked_users()` (только привязанные через deep link).

---

## 11. Что можно сделать иначе средствами Flet

### 9.1 DatePicker вместо текстового поля

Сейчас дата вводится как строка (`TextField(label="Дата", value="2026-03-24")`).
Flet поддерживает нативный выбор даты:

```python
def open_datepicker(e):
    page.open(ft.DatePicker(
        first_date=date(2020, 1, 1),
        last_date=date(2030, 12, 31),
        on_change=lambda e: date_field.set_value(e.control.value),
    ))

date_field = ft.TextField(label="Дата", read_only=True)
ft.IconButton(ft.Icons.CALENDAR_TODAY, on_click=open_datepicker)
```

Это убрало бы необходимость вводить дату вручную и парсить строку.

---

### 9.2 BottomSheet вместо AlertDialog для форм добавления

`AlertDialog` — маленькое модальное окно по центру.
`BottomSheet` — выезжает снизу, как в мобильных приложениях:

```python
bs = ft.BottomSheet(
    ft.Container(
        padding=20,
        content=ft.Column([
            ft.Text("Добавить расход", size=18, weight=ft.FontWeight.BOLD),
            amount_field,
            category_dd,
            ft.ElevatedButton("Добавить", on_click=on_submit),
        ], tight=True),
    ),
    open=True,
)
page.open(bs)
```

Выглядит нативнее для мобильного UI.

---

### 9.3 NavigationBar (встроенный) вместо кастомного nav bar

Сейчас nav bar собирается вручную через `GestureDetector` + `Container` + SVG.
Flet имеет встроенный компонент:

```python
page.navigation_bar = ft.NavigationBar(
    destinations=[
        ft.NavigationBarDestination(icon=ft.Icons.HOME, label="Главная"),
        ft.NavigationBarDestination(icon=ft.Icons.RECEIPT, label="Операции"),
        ft.NavigationBarDestination(icon=ft.Icons.STAR, label="Цели"),
        ft.NavigationBarDestination(icon=ft.Icons.SETTINGS, label="Настройки"),
    ],
    on_change=lambda e: navigate(e.control.selected_index),
)
```

Плюсы: автоматическая анимация, поддержка жестов, адаптируется под платформу.
Минусы: меньше контроля над внешним видом (сложнее подогнать под кастомный дизайн).

---

### 9.4 ListTile вместо ручной сборки строк списка

Сейчас каждая строка транзакции — это вложенный `Container → Row → Row → Column`:

```python
# Сейчас: ~20 строк на один элемент списка
ft.Container(
    content=ft.Row([
        ft.Row([icon_container, ft.Column([name, date])]),
        ft.Row([amount, delete_btn]),
    ], alignment=...)
)

# Альтернатива: ft.ListTile
ft.ListTile(
    leading=icon_container,
    title=ft.Text(category_name),
    subtitle=ft.Text(date),
    trailing=ft.Row([amount_text, delete_btn], tight=True),
)
```

Короче, структурированнее, автоматически выравнивает элементы.

---

### 9.5 Dismissible для свайпа удаления

Вместо кнопки с иконкой корзины — свайп влево для удаления (как в iOS/Android):

```python
ft.Dismissible(
    content=transaction_row,
    direction=ft.DismissDirection.END_TO_START,
    background=ft.Container(bgcolor="#F44336", content=ft.Icon(ft.Icons.DELETE, color="white")),
    on_dismiss=lambda e: delete_transaction(t['id']),
    dismiss_thresholds={ft.DismissDirection.END_TO_START: 0.3},
)
```

---

### 9.6 SegmentedButton для фильтра транзакций

Сейчас фильтр "Все / Доходы / Расходы" — три `ElevatedButton` вручную.
Flet имеет встроенный `SegmentedButton`:

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

---

### 9.7 AnimatedSwitcher для переходов между страницами

Сейчас смена страниц мгновенная. Можно добавить анимацию:

```python
content = ft.AnimatedSwitcher(
    expand=True,
    transition=ft.AnimatedSwitcherTransition.FADE,
    duration=200,
    content=pages[0],
)
# при навигации:
content.content = pages[index]
content.update()
```

---

### 9.8 Хранение сессии — альтернативы session.json

| Подход | Плюсы | Минусы |
|---|---|---|
| `session.json` (сейчас) | Просто, понятно | Файл виден в папке |
| `page.client_storage` | Встроено в Flet, кросс-платформенно | Не работает в старых версиях |
| Строка в таблице `users` (флаг `is_active`) | В БД, не нужен отдельный файл | Не подходит для многопользовательского |
| Keychain/Keystore (через subprocess) | Безопасно | Сложно, платформозависимо |

---

### 9.9 Реактивное состояние вместо ручного refresh()

Сейчас после каждого изменения нужно явно вызывать:
```python
self.refresh()
pages[0].refresh()
page.update()
```

Можно было бы использовать паттерн Observer / reactive store:

```python
class AppStore:
    _listeners: list[callable] = []

    def on_change(self, fn):
        self._listeners.append(fn)

    def notify(self):
        for fn in self._listeners:
            fn()

store = AppStore()
# каждая страница подписывается:
store.on_change(lambda: self.refresh())
# при изменении данных:
add_transaction(...)
store.notify()  # все страницы обновятся автоматически
```

Flet не имеет встроенного state management (в отличие от Flutter с Provider/Riverpod),
поэтому такой паттерн нужно реализовывать самостоятельно.

---

### 11.10 Charts (аналитика) — реализовано

В `pages/analytics.py` используется `flet_charts` (`BarChart` + `LineChart`). Данные берутся из БД через `get_monthly_summary`, `get_expense_breakdown_by_year`, `get_available_years`. Если данных меньше `MIN_MONTHS` — показывается заглушка «Добавьте хотя бы 2 месяца данных».

Цвета категорий — через константный список `CATEGORY_COLORS`; легенда строится автоматически.

---

## 12. Что не хватает в текущей версии

| Функция | Сложность | Нужно для | Статус |
|---|---|---|---|
| DatePicker в диалогах | Низкая | Удобство | TODO |
| Swipe to delete | Низкая | UX | TODO |
| Аналитика с реальными графиками | Средняя | Ключевая идея проекта | ✅ сделано |
| Профиль пользователя (имя) | Низкая | Персонализация | TODO |
| Выбор валюты | Средняя | Затрагивает все страницы | TODO |
| Уведомления о подписках | Высокая | Требует фоновые задачи / планировщик | ✅ сделано (бот) |
| Telegram-бот интеграция | Высокая | Отдельный сервис | ✅ сделано |
| Экспорт данных (CSV/PDF) | Средняя | Отчётность | TODO |
| Тёмная тема / переключатель | Низкая | Комфорт | TODO |
| Мультивалютность | Высокая | Разные счета | TODO |
| Симулятор «что если» | Средняя | Финансовое планирование | ✅ сделано |
| Исправить BUG-1 (Reset без `WHERE user_id`) | Низкая | Безопасность данных | TODO |
| Исправить BUG-2 (дубликаты при изменении баланса) | Средняя | Корректность | TODO |
