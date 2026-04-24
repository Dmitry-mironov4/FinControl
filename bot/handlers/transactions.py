import re
import datetime
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from fincontrolapp.db_queries import (
    get_user_by_telegram_id,
    get_categories,
    add_transaction,
    get_balance,
    get_last_transactions,
    delete_transaction,
)
from bot.utils.categorizer import categorize
from bot.utils.formatters import format_balance, format_transaction
from bot.keyboards.inline import history_keyboard, confirm_delete_tx_keyboard
from bot.handlers.add_dialog import AddTransaction

router = Router()

TRANSACTION_PATTERN = re.compile(r'^([+-])(\d+(?:[.,]\d+)?)\s*(.*)$')
PAGE_SIZE = 10


def _build_history_text(transactions: list, offset: int) -> str:
    if not transactions:
        return "Операций пока нет. Добавь первую!"
    start = offset + 1
    end = offset + len(transactions)
    lines = [f"Операции {start}–{end}:"]
    for t in transactions:
        lines.append(format_transaction(t))
    return "\n".join(lines)


@router.message(~StateFilter(AddTransaction), F.text.regexp(r'^[+-]\d'))
async def handle_quick_transaction(message: Message):
    user = get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала запустите /start")
        return

    match = TRANSACTION_PATTERN.match(message.text.strip())
    if not match:
        return

    sign, amount_str, description = match.groups()
    tx_type = "income" if sign == "+" else "expense"
    amount = float(amount_str.replace(",", "."))
    description = description.strip()

    category_name = categorize(description, tx_type)
    categories = get_categories(type=tx_type)
    category = next((c for c in categories if c["name"] == category_name), None)
    if not category:
        category = next((c for c in categories if c["name"] == "Другое"), categories[0])

    add_transaction(
        user_id=user["id"],
        type=tx_type,
        amount=amount,
        category_id=category["id"],
        description=description or None,
        date=datetime.date.today(),
    )
    balance = get_balance(user["id"])

    amount_str_fmt = f"{amount:,.0f}".replace(",", " ")
    desc_part = f" ({description})" if description else ""

    if tx_type == "expense":
        label = "Расход записан"
        money_emoji = "💸"
    else:
        label = "Доход записан"
        money_emoji = "💰"

    await message.answer(
        f"✅ {label}\n"
        f"{money_emoji} {amount_str_fmt}₽ — {category['name']}{desc_part}\n"
        f"{format_balance(balance)}"
    )


@router.message(Command("history"))
async def cmd_history(message: Message):
    user = get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала запустите /start")
        return

    transactions = get_last_transactions(user["id"], limit=PAGE_SIZE, offset=0)
    has_more = len(transactions) == PAGE_SIZE
    text = _build_history_text(transactions, 0)
    markup = history_keyboard(transactions, 0, has_more) if transactions else None
    await message.answer(text, reply_markup=markup)


@router.callback_query(F.data.startswith("history_page_"))
async def cb_history_page(callback: CallbackQuery):
    offset = int(callback.data.split("_")[-1])
    user = get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Сначала запустите /start", show_alert=True)
        return

    transactions = get_last_transactions(user["id"], limit=PAGE_SIZE, offset=offset)
    has_more = len(transactions) == PAGE_SIZE
    text = _build_history_text(transactions, offset)
    markup = history_keyboard(transactions, offset, has_more) if transactions else None
    await callback.message.edit_text(text, reply_markup=markup)
    await callback.answer()


@router.callback_query(F.data.startswith("del_tx_"))
async def cb_del_tx(callback: CallbackQuery):
    # del_tx_{id}  — спрашиваем подтверждение
    tx_id = int(callback.data.split("_")[-1])
    # определяем текущий offset из текста сообщения (берём из кнопки "Ещё 10" если есть,
    # иначе предполагаем offset=0)
    offset = _get_offset_from_markup(callback.message.reply_markup)
    await callback.message.edit_text(
        f"Удалить операцию #{tx_id}?",
        reply_markup=confirm_delete_tx_keyboard(tx_id, offset),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_del_tx_"))
async def cb_confirm_del_tx(callback: CallbackQuery):
    # confirm_del_tx_{id}_{offset}
    parts = callback.data.split("_")
    tx_id = int(parts[-2])
    offset = int(parts[-1])
    user = get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Сначала запустите /start", show_alert=True)
        return

    deleted = delete_transaction(tx_id, user["id"])
    if not deleted:
        await callback.answer("Операция не найдена", show_alert=True)
        return

    # Перезагружаем страницу (offset может сдвинуться если удалили последний элемент)
    transactions = get_last_transactions(user["id"], limit=PAGE_SIZE, offset=offset)
    if not transactions and offset > 0:
        offset = max(0, offset - PAGE_SIZE)
        transactions = get_last_transactions(user["id"], limit=PAGE_SIZE, offset=offset)
    has_more = len(transactions) == PAGE_SIZE
    text = _build_history_text(transactions, offset)
    markup = history_keyboard(transactions, offset, has_more) if transactions else None
    await callback.message.edit_text(text, reply_markup=markup)
    await callback.answer("Удалено ✅")


def _get_offset_from_markup(markup) -> int:
    """Извлекает текущий offset из callback_data кнопок пагинации."""
    if not markup:
        return 0
    for row in markup.inline_keyboard:
        for btn in row:
            if btn.callback_data and btn.callback_data.startswith("history_page_"):
                raw = int(btn.callback_data.split("_")[-1])
                # "Ещё 10" содержит offset+10, "◀️ Назад" содержит offset-10
                if btn.text.startswith("📋"):
                    return raw - PAGE_SIZE
                if btn.text.startswith("◀️"):
                    return raw + PAGE_SIZE
    return 0
