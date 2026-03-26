from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# кнопка назад
def back_keyboard(action: str):
    buttons = [
        [InlineKeyboardButton(text='Назад', callback_data=f'back_to_{action}')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# главное меню
def main_menu_keyboard():
    buttons = [
        [InlineKeyboardButton(text='Баланс', callback_data='menu_balance')],
        [InlineKeyboardButton(text='Операции', callback_data='menu_operations')],
        [InlineKeyboardButton(text='Подписки', callback_data='menu_subscriptions')],
        [InlineKeyboardButton(text='Профиль', callback_data='menu_profile')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# операции
def operations_keyboard():
    pass

# подписки
def subscriptions_keyboard(action: str):
    buttons = [
        [InlineKeyboardButton(text='Активные', callback_data='sub_active')],
        [InlineKeyboardButton(text='Добавить', callback_data='sub_add')],
        [InlineKeyboardButton(text='Назад', callback_data=f'back_to_{action}')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# профиль
def profile_keyboard(action: str):
    buttons = [
        [InlineKeyboardButton(text='Мои данные', callback_data='profile_data')],
        [InlineKeyboardButton(text='Карты', callback_data='profile_cards')],
        [InlineKeyboardButton(text='Категории', callback_data='profile_categories')],
        [InlineKeyboardButton(text='Цели', callback_data='profile_goals')],
        [InlineKeyboardButton(text='Настройки', callback_data='profile_settings')],
        [InlineKeyboardButton(text='Назад', callback_data=f'back_to_{action}')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# первый вход
def onboarding_keyboard():
    pass

# цели
def goals_keyboard(action: str):
    buttons = [
        [InlineKeyboardButton(text='Новая цель', callback_data='goal_add')],
        [InlineKeyboardButton(text='Мои цели', callback_data='goal_list')],
        [InlineKeyboardButton(text='Назад', callback_data=f'back_to_{action}')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# настройки
def settings_keyboard(action: str):
    buttons = [
        [InlineKeyboardButton(text='Валюта', callback_data='set_currency')],
        [InlineKeyboardButton(text='Уведомления', callback_data='set_notifications')],
        [InlineKeyboardButton(text='Назад', callback_data=f'back_to_{action}')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# подтверждение (да/нет)
def confirm_keyboard(action: str):
    buttons = [
        [InlineKeyboardButton(text='Да', callback_data=f'confirm_{action}')],
        [InlineKeyboardButton(text='Нет', callback_data=f'cancel{action}')],
        [InlineKeyboardButton(text='Назад', callback_data=f'back_to_{action}')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)