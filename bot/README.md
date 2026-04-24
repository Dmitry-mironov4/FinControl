# FinControl — Telegram-бот

Бот для управления личными финансами. Работает поверх базы данных приложения FinControl.

## Стек

- Python 3.11
- aiogram 3
- APScheduler (уведомления)
- SQLite (общая БД с Flet-приложением)

## Структура

```
bot/
├── START_BOT.py              # Точка входа
├── handlers/
│   ├── start.py              # /start, deep link, регистрация по телефону
│   ├── stats.py              # /stats, /help
│   ├── add_dialog.py         # FSM: /add — пошаговое добавление транзакции
│   ├── transactions.py       # Быстрое добавление (+/-), /history, пагинация
│   ├── goals.py              # /goals, FSM пополнения цели
│   ├── subscriptions.py      # /subscriptions
│   ├── menu.py               # Все callback-обработчики инлайн-меню
│   ├── quick_add.py          # Быстрое добавление (cancel_tx callbacks)
│   └── notify.py             # Планировщик уведомлений
├── keyboards/
│   ├── inline.py             # Все инлайн-клавиатуры
│   └── reply.py              # Reply-клавиатура (запрос телефона)
└── utils/
    ├── formatters.py         # fmt_amount, format_balance, format_transaction
    ├── categorizer.py        # Автокатегоризация по описанию
    ├── notifications.py      # notify_subscriptions, notify_goals, notify_budget
    └── scheduler.py          # APScheduler: подписки (10:00 ежедн.), цели/бюджет (пн 10:00)
```

## Запуск

```bash
cd bot
python START_BOT.py
```

Токен задаётся в `bot/.env`:

```
BOT_TOKEN=1234567890:AABBcc...
```

## Команды

| Команда | Описание |
|---------|----------|
| `/start` | Привязать аккаунт (или зарегистрироваться по телефону) |
| `/stats` | Баланс и статистика за текущий месяц |
| `/add` | Добавить транзакцию пошагово (FSM) |
| `/history` | История операций с пагинацией |
| `/goals` | Мои цели + пополнение |
| `/subscriptions` | Активные подписки |
| `/help` | Список команд и формат быстрого ввода |

## Быстрое добавление

Просто напишите сообщение в формате:

```
+5000 зарплата    → доход
-300 кофе         → расход
```

Категория определяется автоматически.

## Привязка аккаунта

1. Откройте приложение FinControl → Настройки → «Подключить Telegram»
2. Перейдите по сформированной ссылке — бот автоматически привяжет аккаунт

Либо: отправьте `/start` и поделитесь номером телефона для регистрации.

## База данных

БД-файл: `fincontrolapp/database.db`. Бот читает и пишет в ту же базу, что и Flet-приложение.
Все запросы к БД — только через `fincontrolapp/db_queries.py`.
