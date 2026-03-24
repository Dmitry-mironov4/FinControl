from aiogram.types import KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def phone_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="Отправить номер", request_contact=True))
    return builder.as_markup(resize_keyboard=True)
