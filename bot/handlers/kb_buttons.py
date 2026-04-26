"""
kb_buttons.py — обработчики кнопок постоянной reply-клавиатуры.
"""
import datetime

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from aiogram.filters import Command
from bot.keyboards.inline import hist_keyboard
from bot.utils.formatters import fmt_amount, MONTH_NAMES
from fincontrolapp.db_queries import (
    get_user_by_telegram_id,
    get_balance,
    get_monthly_summary,
    get_last_transactions,
    get_transactions,
    get_active_timers,
    get_subscriptions,
    get_goals,
)
from bot.utils.formatters import format_transaction
from bot.handlers.add_dialog import AddTransaction
from bot.handlers.purchase_timer import TimerForm
from bot.handlers.subscriptions import _subs_keyboard, _next_charge_date
from bot.handlers.goals import _goals_keyboard, _progress_bar, _format_deadline

router = Router()

HIST_PAGE = 15


def _build_hist_text(txs: list, offset: int, tx_filter: str) -> str:
    label = {"all": "Все операции", "income": "Доходы", "expense": "Расходы"}[tx_filter]
    if not txs:
        return f"📭 {label}: операций нет."
    start = offset + 1
    end = offset + len(txs)
    lines = [f"🗂 {label} ({start}–{end}):"]
    for t in txs:
        lines.append(format_transaction(t))
    return "\n".join(lines)


@router.message(F.text == "💰 Баланс")
async def kb_balance(message: Message):
    user = get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала запустите /start")
        return

    month_name = MONTH_NAMES[datetime.date.today().month].capitalize()
    balance = get_balance(user["id"])
    summary = get_monthly_summary(user["id"])
    income = summary["income"]
    expenses = summary["expenses"]
    savings_rate = round((income - expenses) / income * 100) if income > 0 else 0

    await message.answer(
        f"💰 Баланс: {fmt_amount(balance['balance'])} ₽\n"
        f"─────────────────\n"
        f"📈 Доходы ({month_name}):   {fmt_amount(income)} ₽\n"
        f"📉 Расходы ({month_name}):  {fmt_amount(expenses)} ₽\n"
        f"💼 Норма сбережений:  {savings_rate}%"
    )


@router.message(F.text == "📋 История")
@router.message(Command("history"))
async def kb_history(message: Message):
    user = get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала запустите /start")
        return

    txs = get_last_transactions(user["id"], limit=HIST_PAGE, offset=0)
    has_more = len(txs) == HIST_PAGE
    text = _build_hist_text(txs, 0, "all")
    await message.answer(text, reply_markup=hist_keyboard("all", 0, has_more))


@router.callback_query(F.data == "hist:close")
async def cb_hist_close(callback: CallbackQuery):
    await callback.message.delete()
    await callback.answer()


@router.callback_query(F.data.startswith("hist:"))
async def cb_hist(callback: CallbackQuery):
    user = get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Сначала запустите /start", show_alert=True)
        return

    _, tx_filter, offset_str = callback.data.split(":")
    offset = int(offset_str)

    if tx_filter == "all":
        txs = get_last_transactions(user["id"], limit=HIST_PAGE, offset=offset)
    else:
        txs = get_transactions(user["id"], type_=tx_filter, limit=HIST_PAGE, offset=offset)

    has_more = len(txs) == HIST_PAGE
    text = _build_hist_text(txs, offset, tx_filter)
    await callback.message.edit_text(text, reply_markup=hist_keyboard(tx_filter, offset, has_more))
    await callback.answer()


@router.message(F.text == "➕ Доход")
async def kb_add_income(message: Message, state: FSMContext):
    user = get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала запустите /start")
        return
    await state.update_data(type="income")
    await state.set_state(AddTransaction.amount)
    await message.answer("Введи сумму дохода:")


@router.message(F.text == "➖ Расход")
async def kb_add_expense(message: Message, state: FSMContext):
    user = get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала запустите /start")
        return
    await state.update_data(type="expense")
    await state.set_state(AddTransaction.amount)
    await message.answer("Введи сумму расхода:")


@router.message(F.text == "⏰ Таймер")
async def kb_timer(message: Message):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    user = get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала запустите /start")
        return

    timers = get_active_timers(user["id"])

    if not timers:
        text = "⏰ *Таймеры покупок*\n\nАктивных таймеров нет."
    else:
        lines = ["⏰ *Таймеры покупок*\n"]
        for t in timers:
            remind_at = t["remind_at"][:16]
            status = "🔔 Напомнено" if t["notified"] else f"⏳ {remind_at}"
            lines.append(f"• *{t['item_name']}* — {t['amount']:,.0f} ₽\n  {status}")
        text = "\n".join(lines)

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить таймер", callback_data="timer:add")]
    ])
    await message.answer(text, parse_mode="Markdown", reply_markup=keyboard)


@router.callback_query(F.data == "timer:add")
async def cb_timer_add(callback: CallbackQuery, state: FSMContext):
    user = get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Сначала запустите /start", show_alert=True)
        return
    await state.update_data(user_id=user["id"])
    await callback.message.answer("Что хочешь купить? Введи название товара:")
    await state.set_state(TimerForm.waiting_for_item)
    await callback.answer()


# ─── Подписки и Цели (кнопки клавиатуры) ────────────────────────────────────

@router.message(F.text == "📑 Подписки")
async def kb_subscriptions(message: Message):
    user = get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала запустите /start")
        return
    subs = get_subscriptions(user["id"])
    if not subs:
        await message.answer("У вас нет активных подписок.", reply_markup=_subs_keyboard())
        return
    total = sum(float(s["amount"]) / 12 if s["period"] == "yearly" else float(s["amount"]) for s in subs)
    lines = ["📋 Активные подписки:", ""]
    for s in subs:
        next_date = _next_charge_date(s["charge_day"])
        period = "/год" if s["period"] == "yearly" else "/мес"
        lines.append(f"• {s['name']} — {fmt_amount(float(s['amount']))}₽{period} · спишется {next_date}")
    lines += ["", f"Итого в месяц: {fmt_amount(total)}₽"]
    await message.answer("\n".join(lines), reply_markup=_subs_keyboard())


@router.message(F.text == "🎯 Цели")
async def kb_goals(message: Message):
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    user = get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала запустите /start")
        return
    goals = get_goals(user["id"])
    if not goals:
        add_btn = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить цель", callback_data="goal:add")]
        ])
        await message.answer("У вас пока нет целей.", reply_markup=add_btn)
        return
    lines = ["🎯 Твои цели:", ""]
    for g in goals:
        target = float(g["target_amount"])
        current = float(g["current_amount"])
        pct = min(current / target * 100, 100) if target > 0 else 0
        bar = _progress_bar(pct)
        remaining = max(target - current, 0)
        lines.append(f"🎯 {g['name']}")
        lines.append(f"   {bar} {pct:.0f}% · {fmt_amount(current)} / {fmt_amount(target)}₽")
        if remaining > 0:
            deadline = _format_deadline(g["deadline"])
            lines.append(f"   Осталось: {fmt_amount(remaining)}₽{deadline}")
        else:
            lines.append("   ✅ Цель достигнута!")
        lines.append("")
    await message.answer("\n".join(lines).rstrip(), reply_markup=_goals_keyboard(goals))


