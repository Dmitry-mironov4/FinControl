from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


def phone_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Доход"), KeyboardButton(text="➖ Расход")],
            [KeyboardButton(text="💰 Баланс"), KeyboardButton(text="📋 История")],
            [KeyboardButton(text="🎯 Цели"), KeyboardButton(text="📑 Подписки")],
            [KeyboardButton(text="⏰ Таймер"), KeyboardButton(text="⚙️ Настройки")],
        ],
        resize_keyboard=True,
        is_persistent=True,
    )
