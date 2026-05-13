import datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

from fincontrolapp.db_queries import (
    get_user_by_telegram_id,
    get_last_transactions,
    delete_transaction,
)
from bot.utils.formatters import format_transaction
from bot.keyboards.inline import history_keyboard, confirm_delete_tx_keyboard

router = Router()

PAGE_SIZE = 15


@router.message(Command("history"))
async def cmd_history(message: Message):
    """Алиас: /history → тот же UI, что и кнопка 📋 История."""
    from bot.handlers.kb_buttons import kb_history
    await kb_history(message)


# ─── Пагинация старого /history (обратная совместимость со старыми сообщениями) ──

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
    tx_id = int(callback.data.split("_")[-1])
    offset = _get_offset_from_markup(callback.message.reply_markup)
    await callback.message.edit_text(
        f"Удалить операцию #{tx_id}?",
        reply_markup=confirm_delete_tx_keyboard(tx_id, offset),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_del_tx_"))
async def cb_confirm_del_tx(callback: CallbackQuery):
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

    transactions = get_last_transactions(user["id"], limit=PAGE_SIZE, offset=offset)
    if not transactions and offset > 0:
        offset = max(0, offset - PAGE_SIZE)
        transactions = get_last_transactions(user["id"], limit=PAGE_SIZE, offset=offset)
    has_more = len(transactions) == PAGE_SIZE
    text = _build_history_text(transactions, offset)
    markup = history_keyboard(transactions, offset, has_more) if transactions else None
    await callback.message.edit_text(text, reply_markup=markup)
    await callback.answer("Удалено ✅")


def _build_history_text(transactions: list, offset: int) -> str:
    if not transactions:
        return "Операций пока нет."
    start = offset + 1
    end = offset + len(transactions)
    lines = [f"Операции {start}–{end}:"]
    for t in transactions:
        lines.append(format_transaction(t))
    return "\n".join(lines)


def _get_offset_from_markup(markup) -> int:
    if not markup:
        return 0
    for row in markup.inline_keyboard:
        for btn in row:
            if btn.callback_data and btn.callback_data.startswith("history_page_"):
                raw = int(btn.callback_data.split("_")[-1])
                if btn.text.startswith("📋"):
                    return raw - PAGE_SIZE
                if btn.text.startswith("◀️"):
                    return raw + PAGE_SIZE
    return 0
