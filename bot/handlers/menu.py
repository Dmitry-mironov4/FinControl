import datetime
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from bot.keyboards.inline import main_menu_keyboard, operations_keyboard, subscriptions_keyboard, profile_keyboard
from bot.utils.formatters import format_balance, fmt_amount, format_transaction
from bot.handlers.add_dialog import AddTransaction
from bot.handlers.subscriptions import _next_charge_date
from fincontrolapp.db_queries import (
    get_user_by_telegram_id,
    get_balance,
    get_last_transactions,
    get_subscriptions,
    get_goals,
)

router = Router()


@router.callback_query(F.data == "menu_balance")
async def menu_balance(callback: CallbackQuery):
    user = get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Сначала запустите /start", show_alert=True)
        return
    balance = get_balance(user["id"])
    await callback.message.edit_text(
        format_balance(balance),
        reply_markup=main_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "menu_operations")
async def menu_operations(callback: CallbackQuery):
    user = get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Сначала запустите /start", show_alert=True)
        return
    await callback.message.edit_text(
        "Операции:",
        reply_markup=operations_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "Главное меню:",
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
    name = user.get("username") or user.get("first_name") or "пользователь"
    phone = user.get("phone") or "не указан"
    await callback.message.edit_text(
        f"👤 Профиль\n\nИмя: {name}\nТелефон: {phone}",
        reply_markup=profile_keyboard("menu"),
    )
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
    await callback.message.answer("\n".join(lines), reply_markup=main_menu_keyboard())
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
    total = sum(float(s["amount"]) for s in subs)
    lines = ["📋 Активные подписки:", ""]
    for s in subs:
        next_date = _next_charge_date(s["charge_day"])
        period = "/год" if s.get("period") == "yearly" else "/мес"
        lines.append(f"• {s['name']} — {fmt_amount(float(s['amount']))}₽{period} · спишется {next_date}")
    lines += ["", f"Итого в месяц: {fmt_amount(total)}₽"]
    await callback.message.edit_text(
        "\n".join(lines),
        reply_markup=subscriptions_keyboard("menu"),
    )
    await callback.answer()


@router.callback_query(F.data == "sub_add")
async def sub_add(callback: CallbackQuery):
    await callback.answer("Добавление подписок — в приложении FinControl", show_alert=True)


# --- Профиль ---

@router.callback_query(F.data == "profile_data")
async def profile_data(callback: CallbackQuery):
    user = get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Сначала запустите /start", show_alert=True)
        return
    name = user.get("username") or user.get("first_name") or "не указано"
    phone = user.get("phone") or "не указан"
    created = user.get("created_at", "")
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
    await callback.message.answer("\n".join(lines).rstrip(), reply_markup=profile_keyboard("menu"))
    await callback.answer()


@router.callback_query(F.data.in_({"profile_categories", "profile_settings", "profile_cards"}))
async def profile_stubs(callback: CallbackQuery):
    stubs = {
        "profile_categories": "Управление категориями — в приложении FinControl",
        "profile_settings": "Настройки — в приложении FinControl",
        "profile_cards": "Карты — в приложении FinControl",
    }
    await callback.answer(stubs[callback.data], show_alert=True)
