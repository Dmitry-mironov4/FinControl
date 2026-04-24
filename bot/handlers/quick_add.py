import re
import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from bot.keyboards.inline import cancel_transaction_keyboard
from bot.utils.categorizer import categorize
from bot.utils.formatters import fmt_amount
from fincontrolapp.db_queries import (
    get_user_by_telegram_id,
    get_categories,
    add_transaction,
    delete_transaction,
)

router = Router()

# Формат: «+5000 зарплата» или «-300.50 кофе»
_PATTERN = re.compile(r'^([+-])(\d+(?:[.,]\d+)?)\s+(.+)$', re.DOTALL)


def _find_category_id(category_name: str, tx_type: str) -> int | None:
    """Найти category_id по имени категории; вернуть None если не найдено."""
    cats = get_categories(tx_type)
    for cat in cats:
        if cat['name'].lower() == category_name.lower():
            return cat['id']
    # Попробовать без фильтра по типу (на случай смешанных категорий)
    cats_all = get_categories()
    for cat in cats_all:
        if cat['name'].lower() == category_name.lower():
            return cat['id']
    return None


@router.message(F.text.regexp(r'^[+-]\d'))
async def quick_add_transaction(message: Message):
    user = get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала привяжите аккаунт: /start")
        return

    match = _PATTERN.match(message.text.strip())
    if not match:
        await message.answer("Формат: +1000 описание или -500 описание")
        return

    sign, amount_str, description = match.groups()
    tx_type = 'income' if sign == '+' else 'expense'
    amount = float(amount_str.replace(',', '.'))
    description = description.strip()

    # Автокатегоризация
    category_name = categorize(description, tx_type)
    category_id = _find_category_id(category_name, tx_type)

    tx_id = add_transaction(
        user_id=user['id'],
        type=tx_type,
        amount=amount,
        category_id=category_id,
        description=description,
        date=datetime.date.today(),
    )

    type_label = 'Доход' if tx_type == 'income' else 'Расход'
    sign_label = '+' if tx_type == 'income' else '−'
    desc_display = description.capitalize()

    text = f"✅ Записано: {type_label} {sign_label}{fmt_amount(amount)} ₽ — {desc_display}"
    await message.answer(text, reply_markup=cancel_transaction_keyboard(tx_id))


@router.callback_query(F.data.startswith('cancel_tx_'))
async def cancel_transaction(callback: CallbackQuery):
    tx_id = int(callback.data.split('cancel_tx_')[1])
    deleted = delete_transaction(tx_id)
    if deleted:
        await callback.message.edit_text("❌ Транзакция отменена.")
    else:
        await callback.message.edit_text("Транзакция уже была удалена.")
    await callback.answer()
