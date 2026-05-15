# FinControl

Личный финансовый менеджер: мобильное/десктоп-приложение на **Flet** (Python) с встроенным **Telegram-ботом** для быстрого ввода и уведомлений. Обе части работают поверх одной локальной **SQLite-базы** без внешних серверов. Приложение ведёт учёт доходов, расходов, финансовых целей и подписок, строит аналитику с графиками и позволяет симулировать «что если» сценарии перед принятием финансовых решений.

## Возможности

- Учёт доходов и расходов по категориям
- Финансовые цели с прогрессом и темпом накопления
- Подписки с автосписанием по дню месяца
- Аналитика: помесячные графики доходов/расходов, накопительный баланс, структура расходов по категориям
- Симулятор «что если»: покупка, новая подписка, влияние на цель, сокращение категории
- Telegram-бот: быстрый ввод транзакций, статистика, напоминания о подписках/целях/бюджете

## Стек

| Компонент | Технология |
|---|---|
| UI | Flet 0.85.0, flet-charts 0.85.0 |
| Backend | Python 3.13, SQLite (без ORM) |
| Бот | aiogram 3.27, APScheduler 3.11, Python 3.11 |
| Пакетный менеджер | uv (`pyproject.toml`) |

## Структура репозитория

```
FinControl/
├── fincontrolapp/          # Flet-приложение (источник истины для БД)
│   ├── main.py             # Точка входа, роутер, авто-операции при логине
│   ├── database.py         # Схема БД, миграции, get_connection()
│   ├── db_queries.py       # Плоский SQL-API (используется ботом напрямую)
│   ├── calculations.py     # Чистые финансовые вычисления (симулятор x4)
│   ├── utils.py            # Вспомогательные утилиты
│   ├── pages/              # UI-экраны (по одному файлу на экран)
│   ├── controllers/        # Бизнес-логика экранов
│   ├── components/         # BasePage, AppTheme, диалоги, NavBar
│   ├── modules/            # Слои данных по сущностям
│   │   ├── budgets/        #   model / repository / service
│   │   ├── categories/
│   │   ├── goals/
│   │   ├── subscriptions/
│   │   ├── transactions/
│   │   └── users/
│   └── assets/             # Шрифты (Montserrat x5), иконки SVG, bg.svg
├── bot/                    # Telegram-бот
│   ├── START_BOT.py        # Точка входа бота
│   ├── handlers/           # Роутеры aiogram (start, quick_add, stats, ...)
│   ├── keyboards/          # Reply и inline-клавиатуры
│   └── utils/              # categorizer.py, db_async.py, db_safe.py
├── tests/                  # pytest
├── pyproject.toml          # Зависимости Flet-приложения

```

## Запуск

### Локально (Flet-приложение)

```bash
cd fincontrolapp
uv run python main.py
```

При первом запуске автоматически создаются все таблицы и стартовые категории. Сессия пользователя сохраняется в `fincontrolapp/session.json` — при следующем запуске вход выполняется без пароля.

### iOS / Android (через Flet-приложение на устройстве)

1. Установите официальное приложение **Flet** из App Store / Google Play.
2. Запустите сервер разработки из корня проекта:
   ```bash
   uv run flet run --ios fincontrolapp/main.py
   # или для Android:
   uv run flet run --android fincontrolapp/main.py
   ```
3. Отсканируйте QR-код из приложения Flet на устройстве.

На iOS база данных хранится в `~/Documents/database.db`. Размер окна фиксирован **390×844** — вёрстка заточена под мобильный портрет.

### Telegram-бот

1. Создайте `bot/.env`:
   ```
   BOT_TOKEN=ваш_токен_от_BotFather
   ```
2. Установите зависимости и запустите (отдельный терминал, Python 3.11):
   ```bash
   cd bot
   pip install -r requirements.txt
   python START_BOT.py
   ```

Бот читает ту же SQLite-базу через `fincontrolapp.db_queries`. Отдельной базы у бота нет.

## Архитектурные паттерны

### Template Method — `BasePage`

Все экраны наследуют `BasePage(ft.Container)`. Базовый класс определяет скелет рендеринга: `build_header()` + `build_body()` + `refresh()`. Каждая страница переопределяет только `build_body()` (и при необходимости `build_header()`), не дублируя обвязку.

```
BasePage
├── build_header()   ← опционально переопределяется
├── build_body()     ← обязательно переопределяется
└── refresh()        ← вызывается контроллером после изменений
```

### Repository — `modules/<entity>/`

Каждая сущность имеет три слоя:

| Слой | Файл | Ответственность |
|---|---|---|
| Model | `model.py` | Датакласс сущности |
| Repository | `repository.py` | Параметризованные SQL-запросы |
| Service | `service.py` | Бизнес-правила, валидация |

Бот использует плоский `db_queries.py` напрямую — без модульного слоя.

### DI через `page.data`

Глобальное состояние сессии передаётся через словарь `page.data`, который инициализируется в `main.py` и доступен любому контроллеру или странице:

```python
page.data["user_id"]   # ID текущего пользователя
page.data["navigate"]  # функция навигации между экранами
page.data["logout"]    # функция выхода из аккаунта
page.data["pages"]     # кэш созданных экранов
```

Контроллеры принимают `user_id` через конструктор — зависимости явные, без глобальных синглтонов.

## Навигация

| Индекс | Страница | Nav bar | Откуда открывается |
|---|---|---|---|
| 0 | HomePage | ✅ | — |
| 1 | AnalyticsPage | ✅ | — |
| 2 | GoalsPage | ✅ | — |
| 3 | SettingsPage | ✅ | — |
| 4 | SubscriptionsPage | — | HomePage |
| 5 | IncomePage | — | HomePage |
| 6 | ExpensesPage | — | HomePage |
| 7 | TransactionsPage | — | HomePage |
| 8 | SimulatorPage | ✅ | — |
| 9 | BudgetPage | — | AnalyticsPage |

Страницы создаются лениво — при первом переходе, не при запуске.

## Технические ограничения

- Размер окна фиксирован **390×844** — вёрстка под мобильный портрет, не менять.
- ML-библиотеки (scikit-learn, statsmodels, scipy) несовместимы с мобильной сборкой Flet — не использовать. Прогнозы реализованы через МНК вручную в `calculations.py`.

## База данных

Файл: `fincontrolapp/database.db` (создаётся автоматически).

| Таблица | Назначение |
|---|---|
| `users` | Пользователи: email/телефон, password_hash, telegram_id |
| `categories` | Категории доходов и расходов |
| `transactions` | Доходы и расходы (флаг `is_recurring` для зарплаты) |
| `goals` | Финансовые цели (`target_amount`, `current_amount`, `deadline`) |
| `subscriptions` | Подписки (`charge_day`, `period`, `is_paused`) |
| `budgets` | Лимиты по категориям (`monthly`/`yearly`) |
| `purchase_timers` | Таймеры обдумывания покупок |

Все запросы параметризованы (`?`). Миграции — через `try/except ALTER TABLE` в `database.py`.

## Команда

| Роль | Участник |
|---|---|
| Tech Lead + Bot Owner | Дмитрий |
| Аналитик (User Stories, формулы) | Настя |
| Аналитик (Use Cases, ER) | Вика |
| Дизайнер | Алтана |
