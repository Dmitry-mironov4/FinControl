import datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from fincontrolapp.db_queries import get_user_by_telegram_id, get_goals, deposit_to_goal, add_goal
from bot.utils.formatters import fmt_amount

router = Router()


class GoalDeposit(StatesGroup):
    amount = State()


class GoalForm(StatesGroup):
    name = State()
    target = State()
    deadline = State()


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
    buttons.append([InlineKeyboardButton(text="➕ Добавить цель", callback_data="goal:add")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def _skip_deadline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Пропустить", callback_data="goal_skip_deadline")]
    ])


@router.message(Command("goals"))
async def cmd_goals(message: Message):
    user = get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала запустите /start")
        return

    goals = get_goals(user["id"])
    add_btn = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить цель", callback_data="goal:add")]
    ])

    if not goals:
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

    keyboard = _goals_keyboard(goals)
    await message.answer("\n".join(lines).rstrip(), reply_markup=keyboard)


# ─── Пополнение цели ──────────────────────────────────────────────────────────

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
    user = get_user_by_telegram_id(message.from_user.id)
    await state.clear()

    deposit_to_goal(user["id"], goal_id, amount)
    await message.answer(f"✅ Пополнено на {fmt_amount(amount)}₽")


# ─── Добавление цели ──────────────────────────────────────────────────────────

@router.callback_query(F.data == "goal:add")
async def cb_goal_add(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Название цели (например: Отпуск в Турции):")
    await state.set_state(GoalForm.name)
    await callback.answer()


@router.message(GoalForm.name)
async def goal_got_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("Целевая сумма (например: 150000):")
    await state.set_state(GoalForm.target)


@router.message(GoalForm.target)
async def goal_got_target(message: Message, state: FSMContext):
    try:
        amount = float(message.text.replace(",", ".").strip())
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Введи корректную сумму, например: 150000")
        return
    await state.update_data(target=amount)
    await message.answer(
        "Дедлайн (дд.мм.гггг, например: 31.12.2026)\nИли пропусти:",
        reply_markup=_skip_deadline_keyboard(),
    )
    await state.set_state(GoalForm.deadline)


@router.message(GoalForm.deadline)
async def goal_got_deadline(message: Message, state: FSMContext):
    text = message.text.strip()
    try:
        deadline = datetime.datetime.strptime(text, "%d.%m.%Y").date().isoformat()
    except ValueError:
        await message.answer("Формат: дд.мм.гггг, например 31.12.2026\nИли нажми «Пропустить»")
        return
    await _finish_goal(message, state, deadline)


@router.callback_query(GoalForm.deadline, F.data == "goal_skip_deadline")
async def goal_skip_deadline(callback: CallbackQuery, state: FSMContext):
    await _finish_goal(callback.message, state, deadline=None)
    await callback.answer()


async def _finish_goal(message: Message, state: FSMContext, deadline: str | None):
    data = await state.get_data()
    await state.clear()

    user = get_user_by_telegram_id(message.chat.id)
    if not user:
        await message.answer("Аккаунт не найден. Запустите /start заново.")
        return

    add_goal(
        user_id=user["id"],
        name=data["name"],
        target_amount=data["target"],
        deadline=deadline,
    )

    deadline_str = f"\nДедлайн: {datetime.date.fromisoformat(deadline).strftime('%d.%m.%Y')}" if deadline else ""
    await message.answer(
        f"✅ Цель добавлена!\n"
        f"*{data['name']}* — {fmt_amount(data['target'])}₽{deadline_str}",
        parse_mode="Markdown",
    )
