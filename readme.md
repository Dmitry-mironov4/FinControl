# FinControl

Личный финансовый менеджер: десктоп/мобильное приложение на **Flet** + **Telegram-бот** для быстрого ввода и уведомлений. Обе части работают поверх **одной локальной SQLite-базы**.

## Возможности

- Учёт доходов и расходов по категориям
- Финансовые цели с прогрессом и темпом накопления
- Подписки с автосписанием по дню месяца
- Аналитика: помесячные графики доходов/расходов, накопительный баланс, структура расходов по категориям (`flet_charts`)
- Симулятор «что если»: покупка, новая подписка, влияние на цель, сокращение категории
- Telegram-бот: быстрый ввод транзакций, статистика, напоминания о подписках/целях/бюджете

## Стек

- **Python 3.13+**, **Flet 0.82.0** (UI), **SQLite** (хранилище)
- **aiogram 3** + **APScheduler** для бота (Python 3.11, отдельный venv)
- Менеджер пакетов: **uv**

## Структура репозитория

```
FinControl/
├── fincontrolapp/        # Flet-приложение (источник истины для БД)
│   ├── main.py           # Точка входа
│   ├── database.py       # Схема БД, миграции, get_connection()
│   ├── db_queries.py     # Плоский API запросов (используется ботом)
│   ├── calculations.py   # Чистые финансовые вычисления (симулятор)
│   ├── pages/            # UI-экраны
│   ├── controllers/      # Бизнес-логика
│   ├── components/       # BasePage, AppTheme, диалоги, навбар
│   ├── modules/          # Слои данных по сущностям (model/repository/service)
│   ├── assets/           # Шрифты, иконки, фоны
│   └── database.db       # SQLite (одна БД на проект)
├── bot/                  # Telegram-бот (aiogram 3)
│   ├── START_BOT.py
│   ├── handlers/
│   ├── keyboards/
│   └── utils/
├── pyproject.toml        # Конфигурация Flet-приложения
├── uv.lock
├── ARCHITECTURE.md       # Подробная архитектура и альтернативы
├── CODEBASE.md           # Обзор кодовой базы
├── CLAUDE.md             # Контекст для Claude
└── DISCOVERIES.md        # Журнал открытий по ходу разработки
```

## Запуск

### Flet-приложение

```bash
cd fincontrolapp
uv run python main.py
```

### Запуск под IOS
```bash
uv run flet run --ios fincontrolapp/main.py
```

При первом запуске создаются таблицы и стартовые категории. Сессия сохраняется в `fincontrolapp/session.json` — при следующем запуске вход выполняется автоматически.

Размер окна фиксирован 390×844 (мобильный портрет). Менять не нужно — вёрстка заточена под этот размер.

### Telegram-бот

1. Создайте `bot/.env`:
   ```
   BOT_TOKEN=ваш_токен_от_BotFather
   ```
2. Запуск (из корня проекта, чтобы резолвился импорт `fincontrolapp.*`):
   ```bash
   cd bot && python START_BOT.py
   ```
   `START_BOT.py` сам добавляет родительскую директорию в `sys.path` и стартует APScheduler из `handlers/notify.py`.

Бот ходит в ту же БД, что и приложение, через `from fincontrolapp.db_queries import ...`. Отдельной БД у бота нет.

## Архитектура

**Поток данных в приложении:**
```
Page → Controller → Service → Repository → SQLite
```

- **pages/** — наследники `BasePage(ft.Container)`, переопределяют `build_body()`.
- **controllers/** — связывают страницу и сервисы, инжектируются в `__init__` страницы.
- **modules/<entity>/** — `model.py` (датакласс) + `repository.py` (SQL) + `service.py` (бизнес-логика).
- **db_queries.py** — плоский слой, оставлен для бота и легаси-кода. **Новые страницы** работают через `modules/`.

**Бот:** все вызовы `db_queries.*` оборачиваются в `await run_db(...)` (`bot/utils/db_async.py`), хендлеры покрыты декоратором `@safe_db()` (`bot/utils/db_safe.py`).

Подробнее: [ARCHITECTURE.md](ARCHITECTURE.md), [CODEBASE.md](CODEBASE.md).

## База данных

Файл: `fincontrolapp/database.db` (создаётся автоматически).

Таблицы:

| Таблица | Назначение |
|---|---|
| `users` | Пользователи: email/телефон, password_hash, telegram_id |
| `categories` | Категории доходов и расходов (стартовый набор + миграции) |
| `transactions` | Доходы и расходы (с флагом `is_recurring` для зарплаты) |
| `goals` | Финансовые цели (`target_amount`, `current_amount`, `deadline`) |
| `subscriptions` | Подписки (`charge_day`, `period`, `is_paused`, `last_charged_at`) |

Все запросы — параметризованные (`?`), без f-строк. Миграции — через `try/except ALTER TABLE`.

## Авто-операции при логине

При входе пользователя `main.py` запускает:

1. `_check_and_add_recurring_income(user_id)` — добавляет зарплату, если новый месяц и есть шаблон recurring-зарплаты.
2. `_check_and_charge_subscriptions(user_id)` — списывает подписки, у которых `charge_day` ≤ сегодня и они ещё не списаны в этом периоде.

## Привязка Telegram-аккаунта

В настройках Flet-приложения есть deep link `t.me/<bot>?start=<user_id>`. После перехода бот сохраняет `telegram_id` в запись пользователя и далее работает с этим аккаунтом.

## Тех. ограничения

- Размер окна Flet — фиксирован 390×844.
- ML-библиотеки (scikit-learn, statsmodels, scipy) — несовместимы с мобильной сборкой Flet, не использовать.


## Документация

- [ARCHITECTURE.md](ARCHITECTURE.md) — поток данных, слои, альтернативы
- [CODEBASE.md](CODEBASE.md) — обзор файлов и страниц

