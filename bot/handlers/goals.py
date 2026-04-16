import datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from fincontrolapp.db_queries import get_user_by_telegram_id, get_goals, deposit_to_goal
from bot.utils.formatters import fmt_amount

router = Router()


class GoalDeposit(StatesGroup):
    amount = State()


def _progress_bar(pct: float) -> str:
    filled = round(pct / 10)
    return "█" * filled + "░" * (10 - filled)


def _format_deadline(deadline_str: str | None) -> str:
    if not deadline_str:
        return ""
    try:
        d = datetime.date.fromisoformat(deadline_str)
        return f" · до {d.strftime('%d.%m.%Y')}"
    except ValueError:
        return ""


def _goals_keyboard(goals: list) -> InlineKeyboardMarkup:
    buttons = [
        [InlineKeyboardButton(
            text=f"+ Пополнить «{g['name']}»",
            callback_data=f"goal_deposit_{g['id']}"
        )]
        for g in goals
        if float(g["current_amount"]) < float(g["target_amount"])
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(Command("goals"))
async def cmd_goals(message: Message):
    user = get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала запустите /start")
        return

    goals = get_goals(user["id"])
    if not goals:
        await message.answer("У вас пока нет целей.\nДобавьте цель в приложении FinControl.")
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
            deadline = _format_deadline(g.get("deadline"))
            lines.append(f"   Осталось: {fmt_amount(remaining)}₽{deadline}")
        else:
            lines.append("   ✅ Цель достигнута!")
        lines.append("")

    keyboard = _goals_keyboard(goals)
    await message.answer("\n".join(lines).rstrip(), reply_markup=keyboard if keyboard.inline_keyboard else None)


@router.callback_query(F.data.startswith("goal_deposit_"))
async def start_deposit(callback: CallbackQuery, state: FSMContext):
    goal_id = int(callback.data.removeprefix("goal_deposit_"))
    await state.update_data(goal_id=goal_id)
    await state.set_state(GoalDeposit.amount)
    await callback.message.answer("Введи сумму пополнения:")
    await callback.answer()


@router.message(GoalDeposit.amount)
async def process_deposit(message: Message, state: FSMContext):
    text = message.text.strip().replace(",", ".")
    try:
        amount = float(text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Введи корректную сумму (например: 5000)")
        return

    data = await state.get_data()
    goal_id = data["goal_id"]
    await state.clear()

    deposit_to_goal(goal_id, amount)
    await message.answer(f"✅ Пополнено на {fmt_amount(amount)}₽")
