import datetime
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from bot.keyboards.inline import type_keyboard, categories_keyboard, skip_keyboard, main_menu_keyboard
from fincontrolapp.db_queries import (
    get_user_by_telegram_id,
    get_categories,
    add_transaction,
    get_balance,
)
from bot.utils.formatters import format_balance

router = Router()


class AddTransaction(StatesGroup):
    type = State()
    amount = State()
    category = State()
    description = State()


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    current = await state.get_state()
    if current is None:
        await message.answer("Нет активного диалога.")
        return
    await state.clear()
    await message.answer("❌ Отменено.", reply_markup=main_menu_keyboard())


@router.message(Command("add"))
async def cmd_add(message: Message, state: FSMContext):
    user = get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала запустите /start")
        return
    await state.set_state(AddTransaction.type)
    await message.answer("Доход или расход?", reply_markup=type_keyboard())


@router.callback_query(AddTransaction.type, F.data.in_({"add_type_income", "add_type_expense"}))
async def process_type(callback: CallbackQuery, state: FSMContext):
    tx_type = "income" if callback.data == "add_type_income" else "expense"
    await state.update_data(type=tx_type)
    await state.set_state(AddTransaction.amount)
    await callback.message.edit_text("Введи сумму:")
    await callback.answer()


@router.message(AddTransaction.amount)
async def process_amount(message: Message, state: FSMContext):
    text = message.text.strip().replace(",", ".")
    try:
        amount = float(text)
        if amount <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Введи корректную сумму (например: 500 или 1500.50)")
        return

    await state.update_data(amount=amount)
    data = await state.get_data()
    tx_type = data["type"]

    categories = get_categories(type=tx_type)
    await state.set_state(AddTransaction.category)
    await message.answer("Выбери категорию:", reply_markup=categories_keyboard(categories))


@router.callback_query(AddTransaction.category, F.data.startswith("add_cat_"))
async def process_category(callback: CallbackQuery, state: FSMContext):
    category_id = int(callback.data.removeprefix("add_cat_"))
    data = await state.get_data()
    tx_type = data["type"]

    categories = get_categories(type=tx_type)
    category_name = next((c["name"] for c in categories if c["id"] == category_id), "Другое")

    await state.update_data(category_id=category_id, category_name=category_name)
    await state.set_state(AddTransaction.description)
    await callback.message.edit_text(
        "Описание (или пропусти):",
        reply_markup=skip_keyboard(),
    )
    await callback.answer()


@router.message(AddTransaction.description)
async def process_description(message: Message, state: FSMContext):
    await _finish_add(message, state, description=message.text.strip())


@router.callback_query(AddTransaction.description, F.data == "add_skip_desc")
async def process_skip_description(callback: CallbackQuery, state: FSMContext):
    await _finish_add(callback.message, state, description=None, edit=True)
    await callback.answer()


async def _finish_add(message: Message, state: FSMContext, description, edit=False):
    data = await state.get_data()
    tx_type = data["type"]
    amount = data["amount"]
    category_id = data["category_id"]
    category_name = data["category_name"]

    telegram_id = message.chat.id
    user = get_user_by_telegram_id(telegram_id)
    if not user:
        await state.clear()
        await message.answer("Сначала запустите /start")
        return

    add_transaction(
        user_id=user["id"],
        type=tx_type,
        amount=amount,
        category_id=category_id,
        description=description,
        date=datetime.date.today(),
    )
    balance = get_balance(user["id"])
    await state.clear()

    sign = "+" if tx_type == "income" else "-"
    label = "Доход" if tx_type == "income" else "Расход"
    amount_str = f"{amount:,.0f}".replace(",", " ")
    desc_part = f" ({description})" if description else ""
    text = (
        f"✅ Записано: {sign}{amount_str}₽ {category_name}{desc_part}\n"
        f"{format_balance(balance)}"
    )

    if edit:
        await message.edit_text(text, reply_markup=main_menu_keyboard())
    else:
        await message.answer(text, reply_markup=main_menu_keyboard())
