"""
settings.py — Настройки бота: помощь и время уведомлений.
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from fincontrolapp.db_queries import (
    get_user_by_telegram_id,
    get_notification_hour,
    set_notification_hour,
)

router = Router()

# Доступные часы для уведомлений
NOTIFY_HOURS = [7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22]


def _settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔔 Настройка уведомлений", callback_data="settings:notify")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="settings:help")],
    ])


def _notify_keyboard(current_hour: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for h in NOTIFY_HOURS:
        label = f"✅ {h:02d}:00" if h == current_hour else f"{h:02d}:00"
        builder.button(text=label, callback_data=f"notify_hour:{h}")
    builder.adjust(3)
    builder.row(InlineKeyboardButton(text="← Назад", callback_data="settings:back"))
    return builder.as_markup()


@router.message(F.text == "⚙️ Настройки")
async def kb_settings(message: Message):
    user = get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Сначала запустите /start")
        return
    hour = get_notification_hour(user["id"])
    await message.answer(
        f"⚙️ *Настройки*\n\nУведомления приходят в *{hour:02d}:00*",
        parse_mode="Markdown",
        reply_markup=_settings_keyboard(),
    )


@router.callback_query(F.data == "settings:notify")
async def cb_settings_notify(callback: CallbackQuery):
    user = get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Сначала запустите /start", show_alert=True)
        return
    hour = get_notification_hour(user["id"])
    await callback.message.edit_text(
        f"🔔 *Настройка уведомлений*\n\n"
        f"Выбери время, в которое хочешь получать уведомления.\n"
        f"Сейчас: *{hour:02d}:00*\n\n"
        f"_Уведомления включают:_\n"
        f"• Напоминания о подписках\n"
        f"• Прогресс по целям\n"
        f"• Предупреждения о перерасходе",
        parse_mode="Markdown",
        reply_markup=_notify_keyboard(hour),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("notify_hour:"))
async def cb_set_notify_hour(callback: CallbackQuery):
    user = get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Сначала запустите /start", show_alert=True)
        return
    hour = int(callback.data.split(":")[1])
    set_notification_hour(user["id"], hour)
    await callback.message.edit_text(
        f"🔔 *Настройка уведомлений*\n\n"
        f"✅ Установлено: уведомления в *{hour:02d}:00*\n\n"
        f"_Уведомления включают:_\n"
        f"• Напоминания о подписках\n"
        f"• Прогресс по целям\n"
        f"• Предупреждения о перерасходе",
        parse_mode="Markdown",
        reply_markup=_notify_keyboard(hour),
    )
    await callback.answer(f"✅ Уведомления в {hour:02d}:00")


@router.callback_query(F.data == "settings:back")
async def cb_settings_back(callback: CallbackQuery):
    user = get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer()
        return
    hour = get_notification_hour(user["id"])
    await callback.message.edit_text(
        f"⚙️ *Настройки*\n\nУведомления приходят в *{hour:02d}:00*",
        parse_mode="Markdown",
        reply_markup=_settings_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "settings:help")
async def cb_settings_help(callback: CallbackQuery):
    text = (
        "📖 *Справка FinControl*\n"
        "─────────────────────\n"
        "Кнопки внизу:\n"
        "  ➕ Доход / ➖ Расход — быстрое добавление\n"
        "  💰 Баланс — баланс и статистика за месяц\n"
        "  📋 История — все операции с фильтрами\n"
        "  ⏰ Таймер — антиимпульсный таймер покупки\n\n"
        "Быстрое добавление текстом:\n"
        "`+5000 зарплата`  — доход\n"
        "`-300 кофе`       — расход\n\n"
        "Команды:\n"
        "/goals        — цели и пополнение\n"
        "/subscriptions — подписки\n"
        "/stats        — статистика\n"
        "/cancel       — отменить диалог"
    )
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="← Назад", callback_data="settings:back")]
        ]),
    )
    await callback.answer()
