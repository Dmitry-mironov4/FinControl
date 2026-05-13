from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

PAGE_SIZE = 15


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


def type_keyboard():
    buttons = [
        [
            InlineKeyboardButton(text='Доход', callback_data='add_type_income'),
            InlineKeyboardButton(text='Расход', callback_data='add_type_expense'),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def categories_keyboard(categories: list):
    builder = InlineKeyboardBuilder()
    for cat in categories:
        builder.button(text=cat['name'], callback_data=f'add_cat_{cat["id"]}')
    builder.adjust(2)
    return builder.as_markup()


def skip_keyboard():
    buttons = [
        [InlineKeyboardButton(text='Пропустить', callback_data='add_skip_desc')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def subscriptions_keyboard(action: str):
    buttons = [
        [InlineKeyboardButton(text='Активные', callback_data='sub_active')],
        [InlineKeyboardButton(text='Назад', callback_data=f'back_to_{action}')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def profile_keyboard(action: str):
    buttons = [
        [InlineKeyboardButton(text='Мои данные', callback_data='profile_data')],
        [InlineKeyboardButton(text='Цели', callback_data='profile_goals')],
        [InlineKeyboardButton(text='Назад', callback_data=f'back_to_{action}')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def cancel_transaction_keyboard(tx_id: int):
    buttons = [
        [InlineKeyboardButton(text='Отменить', callback_data=f'cancel_tx_{tx_id}')]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


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


def hist_keyboard(tx_filter: str, offset: int, has_more: bool) -> InlineKeyboardMarkup:
    """Клавиатура для просмотра истории с фильтром по типу и пагинацией."""
    builder = InlineKeyboardBuilder()

    # фильтры
    builder.button(
        text="📈 Доходы" if tx_filter != "income" else "✅ Доходы",
        callback_data="hist:income:0",
    )
    builder.button(
        text="📉 Расходы" if tx_filter != "expense" else "✅ Расходы",
        callback_data="hist:expense:0",
    )
    builder.adjust(2)

    # кнопка назад к полной истории (только когда активен фильтр)
    if tx_filter != "all":
        builder.button(text="← Вся история", callback_data="hist:all:0")
        builder.adjust(2, 1)

    # пагинация
    if offset > 0 or has_more:
        nav = InlineKeyboardBuilder()
        if offset > 0:
            nav.button(text="◀️", callback_data=f"hist:{tx_filter}:{offset - PAGE_SIZE}")
        if has_more:
            nav.button(text="▶️", callback_data=f"hist:{tx_filter}:{offset + PAGE_SIZE}")
        nav.adjust(2)
        builder.attach(nav)

    # закрыть
    builder.row(InlineKeyboardButton(text="✖️ Закрыть", callback_data="hist:close"))

    return builder.as_markup()


def confirm_delete_tx_keyboard(tx_id: int, offset: int) -> InlineKeyboardMarkup:
    buttons = [
        [
            InlineKeyboardButton(text="✅ Удалить", callback_data=f"confirm_del_tx_{tx_id}_{offset}"),
            InlineKeyboardButton(text="❌ Отмена", callback_data=f"history_page_{offset}"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


