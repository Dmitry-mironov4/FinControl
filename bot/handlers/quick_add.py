import asyncio
import re
import datetime

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.types import Message, CallbackQuery

from bot.keyboards.inline import cancel_transaction_keyboard
from bot.utils.formatters import fmt_amount
from fincontrolapp.db_queries import (
    get_user_by_telegram_id,
    get_categories,
    add_transaction,
    delete_transaction,
    get_budget_exceeded_info,
)
from bot.handlers.subscriptions import SubForm
from bot.handlers.purchase_timer import TimerForm
from bot.handlers.goals import GoalForm, GoalDeposit

router = Router()

# Формат: «+500 Категория» или «+500 Категория[разделитель]описание»
_QUICK_PATTERN = re.compile(r'^([+-])(\d+(?:[.,]\d+)?)\s+(\S.*)$', re.DOTALL)
# Хвостовые знаки препинания у слова-категории: «Еда,» → «Еда»
_TRAILING_PUNCT = re.compile(r'[,;:\-—–]+$')
# Ведущие разделители между категорией и описанием: «— метро» → «метро»
_LEADING_SEP = re.compile(r'^[\s,;:\-—–]+')


def parse_quick_input(text: str) -> dict | None:
    """
    Разбирает строку быстрого ввода.
    Формат: <+/-><сумма> <категория>[<разделитель>]<описание>

    Первое слово после суммы — категория (регистр сохраняется).
    Всё остальное — описание. Разделители между ними убираются.

    Примеры:
      "+500 Еда, поели в маке"   → category_raw="Еда",       description="поели в маке"
      "+500 Еда: поели в маке"   → category_raw="Еда",       description="поели в маке"
      "+500 кофе"                → category_raw="кофе",      description=""
      "-1200 Транспорт — метро"  → category_raw="Транспорт", description="метро"
      "+500 Еда поели в маке"    → category_raw="Еда",       description="поели в маке"
    """
    m = _QUICK_PATTERN.match(text.strip())
    if not m:
        return None

    sign, amount_str, rest = m.groups()
    amount = float(amount_str.replace(',', '.'))
    tx_type = 'income' if sign == '+' else 'expense'

    # Первое слово — категория (убираем хвостовые разделители типа «Еда,»)
    parts = rest.split(None, 1)
    category_raw = _TRAILING_PUNCT.sub('', parts[0])

    # Остаток — убираем ведущие разделители («— метро» → «метро»)
    tail = parts[1] if len(parts) > 1 else ''
    description = _LEADING_SEP.sub('', tail).strip()

    return {
        'amount': amount,
        'tx_type': tx_type,
        'category_raw': category_raw,
        'description': description,
    }


def _find_category(category_raw: str, tx_type: str):
    """Ищет категорию по имени (регистронезависимо). Fallback — «Другое»."""
    cats = get_categories(type_=tx_type)
    for cat in cats:
        if cat['name'].lower() == category_raw.lower():
            return cat
    return next((c for c in cats if c['name'] == 'Другое'), cats[0] if cats else None)


@router.message(
    ~StateFilter(SubForm, TimerForm, GoalForm, GoalDeposit),
    F.text.regexp(r'^[+-]\d'),
)
async def quick_add_transaction(message: Message):
    user = get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала привяжите аккаунт: /start")
        return

    parsed = parse_quick_input(message.text.strip())
    if not parsed:
        await message.answer(
            "Формат: <code>+1000 Категория</code> или <code>+1000 Категория описание</code>",
            parse_mode="HTML",
        )
        return

    tx_type = parsed['tx_type']
    amount = parsed['amount']
    category_raw = parsed['category_raw']
    description = parsed['description'] or None

    category = _find_category(category_raw, tx_type)
    if not category:
        await message.answer("Не удалось найти категорию. Используй кнопки ➕ Доход / ➖ Расход.")
        return

    tx_id = add_transaction(
        user_id=user['id'],
        type_=tx_type,
        amount=amount,
        category_id=category['id'],
        description=description,
        date=datetime.date.today(),
    )

    type_label = 'Доход' if tx_type == 'income' else 'Расход'
    sign_label = '+' if tx_type == 'income' else '−'
    desc_display = f" — {description.capitalize()}" if description else ""

    await message.answer(
        f"✅ {type_label}: {sign_label}{fmt_amount(amount)} ₽\n"
        f"📂 {category['name']}{desc_display}",
        reply_markup=cancel_transaction_keyboard(tx_id),
    )

    # Проверка превышения бюджета при расходе
    if tx_type == 'expense':
        exceeded = await asyncio.to_thread(get_budget_exceeded_info, user['id'], category['id'])
        if exceeded:
            pct = exceeded["pct"]
            emoji = "🔴" if pct >= 100 else "🟡"
            await message.answer(
                f"{emoji} *Внимание!* Лимит по «{exceeded['category_name']}» "
                f"{'превышен' if pct >= 100 else 'почти исчерпан'} "
                f"({pct:.0f}%: {exceeded['spent']:,.0f} / {exceeded['limit']:,.0f} ₽)",
                parse_mode="Markdown",
            )


@router.callback_query(F.data.startswith('cancel_tx_'))
async def cancel_transaction(callback: CallbackQuery):
    tx_id = int(callback.data.split('cancel_tx_')[1])
    user = get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Сначала запустите /start", show_alert=True)
        return
    deleted = delete_transaction(tx_id, user_id=user['id'])
    if deleted:
        await callback.message.edit_text("❌ Транзакция отменена.")
    else:
        await callback.message.edit_text("Транзакция уже была удалена.")
    await callback.answer()
