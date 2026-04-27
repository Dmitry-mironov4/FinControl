"""
purchase_timer.py — Telegram-handler для таймеров антиимпульсных покупок.

Команда /timer запускает создание таймера.
После срабатывания таймера пользователь выбирает:
  🎯 В цель    — пополнить одну из целей на сумму покупки
  💳 Купил сразу — добавить расход в историю
  ❌ Передумал  — ничего не делать
"""
import asyncio
import datetime
import logging

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
    get_purchase_timer,
    set_purchase_timer_decision,
    get_goals,
    deposit_to_goal,
    add_transaction,
    get_categories,
)
from bot.utils.formatters import fmt_amount

logger = logging.getLogger(__name__)
router = Router()


class TimerForm(StatesGroup):
    waiting_for_item = State()
    waiting_for_amount = State()
    waiting_for_hours = State()


# ─── Создание таймера ─────────────────────────────────────────────────────────

@router.message(Command("timer"))
async def cmd_timer(message: Message, state: FSMContext):
    user = await asyncio.to_thread(get_user_by_telegram_id, message.from_user.id)
    if not user:
        await message.answer("Сначала привяжи аккаунт FinControl через приложение (/start).")
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

    remind_at = (datetime.datetime.now() + datetime.timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
    await asyncio.to_thread(create_purchase_timer, data["user_id"], data["item_name"], data["amount"], remind_at)

    await message.answer(
        f"⏰ Таймер установлен!\n"
        f"Товар: *{data['item_name']}*\n"
        f"Цена: *{fmt_amount(data['amount'])} ₽*\n"
        f"Напомню через {hours} ч. ({remind_at[:16]})",
        parse_mode="Markdown",
    )


# ─── Клавиатуры ───────────────────────────────────────────────────────────────

def make_decision_keyboard(timer_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🎯 В цель", callback_data=f"timer_to_goal:{timer_id}"),
            InlineKeyboardButton(text="💳 Купил сразу", callback_data=f"timer_bought_now:{timer_id}"),
        ],
        [InlineKeyboardButton(text="❌ Передумал", callback_data=f"timer_cancelled:{timer_id}")],
    ])


def _goals_pick_keyboard(timer_id: int, goals: list) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(
            text=f"🎯 {g['name']} ({fmt_amount(float(g['current_amount']))} / {fmt_amount(float(g['target_amount']))}₽)",
            callback_data=f"timer_goal_pick:{timer_id}:{g['id']}",
        )]
        for g in goals
        if float(g["current_amount"]) < float(g["target_amount"])
    ]
    buttons.append([InlineKeyboardButton(text="← Назад", callback_data=f"timer_decision_back:{timer_id}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ─── Обработчики решений ──────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("timer_cancelled:"))
async def cb_cancelled(call: CallbackQuery):
    timer_id = int(call.data.split(":")[1])
    await asyncio.to_thread(set_purchase_timer_decision, timer_id, "cancelled")
    await call.message.edit_text(
        call.message.text + "\n\n❌ *Молодец! Сэкономил деньги.*",
        parse_mode="Markdown",
    )
    await call.answer()


@router.callback_query(F.data.startswith("timer_bought_now:"))
async def cb_bought_now(call: CallbackQuery):
    """Купил сразу — добавляет расход в историю."""
    timer_id = int(call.data.split(":")[1])
    timer = await asyncio.to_thread(get_purchase_timer, timer_id)
    if not timer:
        await call.answer("Таймер не найден", show_alert=True)
        return

    # Находим категорию «Покупки»
    categories = await asyncio.to_thread(get_categories, "expense")
    cat = next((c for c in categories if c["name"] == "Покупки"), categories[0] if categories else None)
    if not cat:
        await call.answer("Не найдена категория расходов", show_alert=True)
        return

    today = datetime.date.today().isoformat()
    await asyncio.to_thread(
        add_transaction,
        timer["user_id"], "expense", float(timer["amount"]),
        cat["id"], timer["item_name"], today,
    )
    await asyncio.to_thread(set_purchase_timer_decision, timer_id, "bought")

    await call.message.edit_text(
        call.message.text + f"\n\n💳 *Куплено! Расход {fmt_amount(float(timer['amount']))} ₽ добавлен в историю.*",
        parse_mode="Markdown",
    )
    await call.answer()


@router.callback_query(F.data.startswith("timer_to_goal:"))
async def cb_to_goal(call: CallbackQuery):
    """Показать список целей для пополнения."""
    timer_id = int(call.data.split(":")[1])
    timer = await asyncio.to_thread(get_purchase_timer, timer_id)
    if not timer:
        await call.answer("Таймер не найден", show_alert=True)
        return

    goals = await asyncio.to_thread(get_goals, timer["user_id"])
    active = [g for g in goals if float(g["current_amount"]) < float(g["target_amount"])]

    if not active:
        await call.answer("У тебя нет активных целей", show_alert=True)
        return

    await call.message.edit_text(
        f"🎯 В какую цель положить *{fmt_amount(float(timer['amount']))} ₽*?",
        parse_mode="Markdown",
        reply_markup=_goals_pick_keyboard(timer_id, active),
    )
    await call.answer()


@router.callback_query(F.data.startswith("timer_goal_pick:"))
async def cb_goal_pick(call: CallbackQuery):
    """Пополнить выбранную цель и показать все цели."""
    _, timer_id_str, goal_id_str = call.data.split(":")
    timer_id = int(timer_id_str)
    goal_id = int(goal_id_str)

    timer = await asyncio.to_thread(get_purchase_timer, timer_id)
    if not timer:
        await call.answer("Таймер не найден", show_alert=True)
        return

    amount = float(timer["amount"])
    user_id = timer["user_id"]

    await asyncio.to_thread(deposit_to_goal, user_id, goal_id, amount)
    await asyncio.to_thread(set_purchase_timer_decision, timer_id, "bought")

    # Показываем все цели с прогрессом
    from bot.handlers.goals import _send_goals_summary
    await call.message.edit_text(
        f"✅ *{fmt_amount(amount)} ₽* добавлено в цель!",
        parse_mode="Markdown",
    )
    await _send_goals_summary(call.message, user_id)
    await call.answer()


@router.callback_query(F.data.startswith("timer_decision_back:"))
async def cb_decision_back(call: CallbackQuery):
    """Вернуться к исходным кнопкам таймера."""
    timer_id = int(call.data.split(":")[1])
    timer = await asyncio.to_thread(get_purchase_timer, timer_id)
    if not timer:
        await call.answer()
        return
    await call.message.edit_reply_markup(reply_markup=make_decision_keyboard(timer_id))
    await call.answer()
