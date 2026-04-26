"""
purchase_timer.py — Telegram-handler для таймеров антиимпульсных покупок.

Команда /timer запускает создание таймера через бота.
Inline-кнопки обрабатывают решение: ✅ Купил / ❌ Передумал.
"""
import asyncio
import logging
from datetime import datetime, timedelta

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton,
)

from fincontrolapp.db_queries import (
    get_user_by_telegram_id,
    create_purchase_timer,
    set_purchase_timer_decision,
)

logger = logging.getLogger(__name__)
router = Router()


class TimerForm(StatesGroup):
    waiting_for_item = State()
    waiting_for_amount = State()
    waiting_for_hours = State()


@router.message(Command("timer"))
async def cmd_timer(message: Message, state: FSMContext):
    """Начать создание таймера покупки."""
    user = await asyncio.to_thread(get_user_by_telegram_id, message.from_user.id)
    if not user:
        await message.answer(
            "Сначала привяжи аккаунт FinControl через приложение (/start)."
        )
        return

    await state.update_data(user_id=user["id"])
    await message.answer("Что хочешь купить? Введи название товара:")
    await state.set_state(TimerForm.waiting_for_item)


@router.message(TimerForm.waiting_for_item)
async def got_item(message: Message, state: FSMContext):
    await state.update_data(item_name=message.text.strip())
    await message.answer("Сколько это стоит? Введи сумму (например: 2500):")
    await state.set_state(TimerForm.waiting_for_amount)


@router.message(TimerForm.waiting_for_amount)
async def got_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", ".").strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Введи корректную сумму, например: 2500")
        return

    await state.update_data(amount=amount)
    await message.answer("Через сколько часов напомнить? Введи число (например: 24):")
    await state.set_state(TimerForm.waiting_for_hours)


@router.message(TimerForm.waiting_for_hours)
async def got_hours(message: Message, state: FSMContext):
    try:
        hours = int(message.text.strip())
        if hours <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Введи целое число часов, например: 24")
        return

    data = await state.get_data()
    await state.clear()

    remind_at = (datetime.now() + timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")

    await asyncio.to_thread(
        create_purchase_timer,
        data["user_id"], data["item_name"], data["amount"], remind_at,
    )

    await message.answer(
        f"⏰ Таймер установлен!\n"
        f"Товар: *{data['item_name']}*\n"
        f"Цена: *{data['amount']:,.0f} ₽*\n"
        f"Напомню через {hours} ч. ({remind_at[:16]})",
        parse_mode="Markdown",
    )


def make_decision_keyboard(timer_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Купил", callback_data=f"timer_bought:{timer_id}"),
        InlineKeyboardButton(text="❌ Передумал", callback_data=f"timer_cancelled:{timer_id}"),
    ]])


@router.callback_query(F.data.startswith("timer_bought:"))
async def cb_bought(call: CallbackQuery):
    timer_id = int(call.data.split(":")[1])
    await asyncio.to_thread(set_purchase_timer_decision, timer_id, "bought")
    await call.message.edit_text(
        call.message.text + "\n\n✅ *Принято: ты купил это!*",
        parse_mode="Markdown",
    )
    await call.answer()


@router.callback_query(F.data.startswith("timer_cancelled:"))
async def cb_cancelled(call: CallbackQuery):
    timer_id = int(call.data.split(":")[1])
    await asyncio.to_thread(set_purchase_timer_decision, timer_id, "cancelled")
    await call.message.edit_text(
        call.message.text + "\n\n❌ *Молодец! Сэкономил деньги.*",
        parse_mode="Markdown",
    )
    await call.answer()
