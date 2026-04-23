from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

PAGE_SIZE = 10

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
    buttons = [
        [
            InlineKeyboardButton(text='➕ Доход', callback_data='op_add_income'),
            InlineKeyboardButton(text='➖ Расход', callback_data='op_add_expense'),
        ],
        [InlineKeyboardButton(text='📋 История', callback_data='op_history')],
        [InlineKeyboardButton(text='Назад', callback_data='back_to_main')],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# выбор типа транзакции (доход/расход)
def type_keyboard():
    buttons = [
        [
            InlineKeyboardButton(text='Доход', callback_data='add_type_income'),
            InlineKeyboardButton(text='Расход', callback_data='add_type_expense'),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# список категорий
def categories_keyboard(categories: list):
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(text=cat['name'], callback_data=f'add_cat_{cat["id"]}')
    builder.adjust(2)
    return builder.as_markup()

# кнопка "пропустить"
def skip_keyboard():
    buttons = [
        [InlineKeyboardButton(text='Пропустить', callback_data='add_skip_desc')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# подписки
def subscriptions_keyboard(action: str):
    buttons = [
        [InlineKeyboardButton(text='Активные', callback_data='sub_active')],
        [InlineKeyboardButton(text='Назад', callback_data=f'back_to_{action}')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# профиль
def profile_keyboard(action: str):
    buttons = [
        [InlineKeyboardButton(text='Мои данные', callback_data='profile_data')],
        [InlineKeyboardButton(text='Цели', callback_data='profile_goals')],
        [InlineKeyboardButton(text='Назад', callback_data=f'back_to_{action}')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

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

# отмена быстро добавленной транзакции
def cancel_transaction_keyboard(tx_id: int):
    buttons = [
        [InlineKeyboardButton(text='Отменить', callback_data=f'cancel_tx_{tx_id}')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# история транзакций с пагинацией
def history_keyboard(transactions: list, offset: int, has_more: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for i, t in enumerate(transactions, start=1):
        builder.button(
            text=f"🗑 #{offset + i}",
            callback_data=f"del_tx_{t['id']}",
        )
    builder.adjust(5)

    if offset > 0 or has_more:
        nav = InlineKeyboardBuilder()
        if offset > 0:
            nav.button(text="◀️ Назад", callback_data=f"history_page_{offset - PAGE_SIZE}")
        if has_more:
            nav.button(text=f"📋 Ещё {PAGE_SIZE}", callback_data=f"history_page_{offset + len(transactions)}")
        nav.adjust(2)
        builder.attach(nav)

    return builder.as_markup()


# подтверждение удаления транзакции
def confirm_delete_tx_keyboard(tx_id: int, offset: int) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="✅ Удалить", callback_data=f"confirm_del_tx_{tx_id}_{offset}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data=f"history_page_{offset}"),
        ]
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