import datetime
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot.keyboards.inline import main_menu_keyboard, operations_keyboard, subscriptions_keyboard, profile_keyboard
from bot.utils.formatters import format_balance, fmt_amount, format_transaction, MONTH_NAMES, MONTH_SHORT
from bot.handlers.add_dialog import AddTransaction
from bot.handlers.subscriptions import _next_charge_date
from fincontrolapp.db_queries import (
    get_user_by_telegram_id,
    get_balance,
    get_monthly_summary,
    get_last_transactions,
    get_subscriptions,
    get_goals,
)

router = Router()


def _fmt_tx_line(t) -> str:
    """📈 22 апр  +5 000 ₽  Зарплата"""
    try:
        tx_date = datetime.date.fromisoformat(t["date"])
        date_str = f"{tx_date.day} {MONTH_SHORT[tx_date.month]}"
    except (ValueError, TypeError):
        date_str = str(t["date"] or "")

    amount_str = fmt_amount(float(t["amount"]))
    category = t["category_name"] or ""
    emoji, sign = ("📈", "+") if t["type"] == "income" else ("📉", "−")
    return f"{emoji} {date_str}  {sign}{amount_str} ₽  {category}"


@router.callback_query(F.data == "menu_balance")
async def menu_balance(callback: CallbackQuery):
    user = get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Сначала запустите /start", show_alert=True)
        return

    month_name = MONTH_NAMES[datetime.date.today().month].capitalize()
    balance = get_balance(user["id"])
    summary = get_monthly_summary(user["id"])
    income = summary["income"]
    expenses = summary["expenses"]
    savings_rate = round((income - expenses) / income * 100) if income > 0 else 0

    text = (
        f"💰 Баланс: {fmt_amount(balance)} ₽\n"
        f"─────────────────\n"
        f"📈 Доходы ({month_name}):   {fmt_amount(income)} ₽\n"
        f"📉 Расходы ({month_name}):  {fmt_amount(expenses)} ₽\n"
        f"💼 Норма сбережений:  {savings_rate}%"
    )
    await callback.message.edit_text(text, reply_markup=main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "menu_operations")
async def menu_operations(callback: CallbackQuery):
    user = get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Сначала запустите /start", show_alert=True)
        return

    txs = get_last_transactions(user["id"], limit=10)
    if not txs:
        text = "📭 Операций пока нет."
    else:
        lines = [_fmt_tx_line(t) for t in txs]
        text = "🗂 Последние операции:\n\n" + "\n".join(lines)

    await callback.message.edit_text(text, reply_markup=operations_keyboard())
    await callback.answer()


@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    user = get_user_by_telegram_id(callback.from_user.id)
    name = user["username"] if user else callback.from_user.first_name
    await callback.message.edit_text(
        f"👋 Привет, {name}! Выберите раздел:",
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "menu_subscriptions")
async def menu_subscriptions(callback: CallbackQuery):
    user = get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Сначала запустите /start", show_alert=True)
        return
    await callback.message.edit_text(
        "Подписки:",
        reply_markup=subscriptions_keyboard("menu"),
    )
    await callback.answer()


@router.callback_query(F.data == "menu_profile")
async def menu_profile(callback: CallbackQuery):
    user = get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Сначала запустите /start", show_alert=True)
        return

    name = user["username"] or callback.from_user.first_name or "—"
    try:
        created_date = datetime.date.fromisoformat(str(user["created_at"])[:10])
        created_str = f"{created_date.day} {MONTH_SHORT[created_date.month]} {created_date.year}"
    except Exception:
        created_str = "—"

    text = (
        f"👤 Профиль\n"
        f"─────────────────\n"
        f"Имя:         {name}\n"
        f"В системе с: {created_str}"
    )
    await callback.message.edit_text(text, reply_markup=profile_keyboard("menu"))
    await callback.answer()


# --- Операции ---

@router.callback_query(F.data == "op_add_income")
async def op_add_income(callback: CallbackQuery, state: FSMContext):
    user = get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Сначала запустите /start", show_alert=True)
        return
    await state.update_data(type="income")
    await state.set_state(AddTransaction.amount)
    await callback.message.edit_text("Введи сумму дохода:")
    await callback.answer()


@router.callback_query(F.data == "op_add_expense")
async def op_add_expense(callback: CallbackQuery, state: FSMContext):
    user = get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Сначала запустите /start", show_alert=True)
        return
    await state.update_data(type="expense")
    await state.set_state(AddTransaction.amount)
    await callback.message.edit_text("Введи сумму расхода:")
    await callback.answer()


@router.callback_query(F.data == "op_history")
async def op_history(callback: CallbackQuery):
    user = get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Сначала запустите /start", show_alert=True)
        return
    transactions = get_last_transactions(user["id"], limit=10)
    if not transactions:
        await callback.answer("Операций пока нет", show_alert=True)
        return
    lines = ["Последние 10 операций:"]
    for t in transactions:
        lines.append(format_transaction(t))
    await callback.message.edit_text("\n".join(lines), reply_markup=operations_keyboard())
    await callback.answer()


# --- Подписки ---

@router.callback_query(F.data == "sub_active")
async def sub_active(callback: CallbackQuery):
    user = get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Сначала запустите /start", show_alert=True)
        return
    subs = get_subscriptions(user["id"])
    if not subs:
        await callback.message.edit_text(
            "У вас нет активных подписок.\nДобавьте подписку в приложении FinControl.",
            reply_markup=subscriptions_keyboard("menu"),
        )
        await callback.answer()
        return
    total = sum(float(s["amount"]) / 12 if s["period"] == "yearly" else float(s["amount"]) for s in subs)
    lines = ["📋 Активные подписки:", ""]
    for s in subs:
        next_date = _next_charge_date(s["charge_day"])
        period = "/год" if s["period"] == "yearly" else "/мес"
        lines.append(f"• {s['name']} — {fmt_amount(float(s['amount']))}₽{period} · спишется {next_date}")
    lines += ["", f"Итого в месяц: {fmt_amount(total)}₽"]
    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=subscriptions_keyboard("menu"),
    )
    await callback.answer()


# --- Профиль ---

@router.callback_query(F.data == "profile_data")
async def profile_data(callback: CallbackQuery):
    user = get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Сначала запустите /start", show_alert=True)
        return
    name = user["username"] or user["first_name"] or "не указано"
    phone = user["phone"] or "не указан"
    created = user["created_at"] or ""
    if created:
        try:
            d = datetime.date.fromisoformat(created[:10])
            created = d.strftime("%d.%m.%Y")
        except ValueError:
            pass
    text = f"👤 Мои данные\n\nИмя: {name}\nТелефон: {phone}\nДата регистрации: {created or '—'}"
    await callback.message.edit_text(text, reply_markup=profile_keyboard("menu"))
    await callback.answer()


@router.callback_query(F.data == "profile_goals")
async def profile_goals(callback: CallbackQuery):
    user = get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Сначала запустите /start", show_alert=True)
        return
    goals = get_goals(user["id"])
    if not goals:
        await callback.answer("У вас пока нет целей. Добавьте цель в приложении FinControl.", show_alert=True)
        return
    lines = ["🎯 Твои цели:", ""]
    for g in goals:
        target = float(g["target_amount"])
        current = float(g["current_amount"])
        pct = min(current / target * 100, 100) if target > 0 else 0
        filled = round(pct / 10)
        bar = "█" * filled + "░" * (10 - filled)
        remaining = max(target - current, 0)
        lines.append(f"🎯 {g['name']}")
        lines.append(f"   {bar} {pct:.0f}% · {fmt_amount(current)} / {fmt_amount(target)}₽")
        if remaining > 0:
            lines.append(f"   Осталось: {fmt_amount(remaining)}₽")
        else:
            lines.append("   ✅ Цель достигнута!")
        lines.append("")
    await callback.message.edit_text("\n".join(lines).rstrip(), reply_markup=profile_keyboard("menu"))
    await callback.answer()


