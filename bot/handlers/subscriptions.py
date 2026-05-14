import calendar
import datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from fincontrolapp.db_queries import get_user_by_telegram_id, get_subscriptions, add_subscription
from bot.utils.formatters import fmt_amount, MONTH_SHORT

router = Router()


class SubForm(StatesGroup):
    name = State()
    amount = State()
    charge_day = State()
    period = State()


def _next_charge_date(charge_day: int) -> str:
    today = datetime.date.today()

    last_day_this = calendar.monthrange(today.year, today.month)[1]
    day_this = min(charge_day, last_day_this)
    candidate = today.replace(day=day_this)

    if candidate < today:
        if today.month == 12:
            next_year, next_month = today.year + 1, 1
        else:
            next_year, next_month = today.year, today.month + 1
        last_day_next = calendar.monthrange(next_year, next_month)[1]
        day_next = min(charge_day, last_day_next)
        candidate = datetime.date(next_year, next_month, day_next)

    return f"{candidate.day} {MONTH_SHORT[candidate.month]}"


def _subs_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить подписку", callback_data="sub:add")]
    ])


def _period_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📅 Ежемесячно", callback_data="sub_period:monthly"),
            InlineKeyboardButton(text="📆 Ежегодно", callback_data="sub_period:yearly"),
        ]
    ])


@router.message(Command("subscriptions"))
async def cmd_subscriptions(message: Message):
    user = get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала запустите /start")
        return

    subs = get_subscriptions(user["id"])
    if not subs:
        await message.answer(
            "У вас нет активных подписок.",
            reply_markup=_subs_keyboard(),
        )
        return

    total = sum(float(s["amount"]) / 12 if s["period"] == "yearly" else float(s["amount"]) for s in subs)
    lines = ["📋 Активные подписки:", ""]
    for s in subs:
        next_date = _next_charge_date(s["charge_day"])
        period = "/год" if s["period"] == "yearly" else "/мес"
        lines.append(f"• {s['name']} — {fmt_amount(float(s['amount']))}₽{period} · спишется {next_date}")

    lines.append("")
    lines.append(f"Итого в месяц: {fmt_amount(total)}₽")

    await message.answer("\n".join(lines), reply_markup=_subs_keyboard())


# ─── Добавление подписки ──────────────────────────────────────────────────────

@router.callback_query(F.data == "sub:add")
async def cb_sub_add(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Название подписки (например: Netflix):")
    await state.set_state(SubForm.name)
    await callback.answer()


@router.message(SubForm.name)
async def sub_got_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("Сумма списания (например: 599):")
    await state.set_state(SubForm.amount)


@router.message(SubForm.amount)
async def sub_got_amount(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", ".").strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Введи корректную сумму, например: 599")
        return
    await state.update_data(amount=amount)
    await message.answer("День месяца списания (1–31, например: 15):")
    await state.set_state(SubForm.charge_day)


@router.message(SubForm.charge_day)
async def sub_got_day(message: Message, state: FSMContext):
    try:
        day = int(message.text.strip())
        if not 1 <= day <= 31:
            raise ValueError
    except ValueError:
        await message.answer("Введи число от 1 до 31")
        return
    await state.update_data(charge_day=day)
    await message.answer("Период оплаты:", reply_markup=_period_keyboard())
    await state.set_state(SubForm.period)


@router.callback_query(SubForm.period, F.data.startswith("sub_period:"))
async def sub_got_period(callback: CallbackQuery, state: FSMContext):
    period = callback.data.split(":")[1]
    data = await state.get_data()
    await state.clear()

    user = get_user_by_telegram_id(callback.from_user.id)
    add_subscription(
        user_id=user["id"],
        name=data["name"],
        amount=data["amount"],
        charge_day=data["charge_day"],
        period=period,
        start_date=datetime.date.today().isoformat(),
    )

    period_label = "ежегодно" if period == "yearly" else "ежемесячно"
    next_date = _next_charge_date(data["charge_day"])
    await callback.message.edit_text(
        f"✅ Подписка добавлена!\n"
        f"*{data['name']}* — {fmt_amount(data['amount'])}₽ {period_label}\n"
        f"Следующее списание: {next_date}",
        parse_mode="Markdown",
    )
    await callback.answer()
