from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import Command

from bot.keyboards.reply import phone_keyboard, main_keyboard
from fincontrolapp.db_queries import (
    get_user_by_telegram_id,
    create_user,
    update_user_phone,
    link_telegram_to_user_by_id,
    get_user_by_id,
)

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    args = message.text.split()
    deep_link_user_id = args[1] if len(args) > 1 else None

    telegram_id = message.from_user.id
    user = get_user_by_telegram_id(telegram_id)

    if user:
        await message.answer(
            f"👋 С возвращением, {user['username'] or message.from_user.first_name}!",
            reply_markup=main_keyboard(),
        )
        return

    if deep_link_user_id and deep_link_user_id.isdigit():
        user_id_from_app = int(deep_link_user_id)
        user_from_app = get_user_by_id(user_id_from_app)

        if user_from_app:
            existing_tg = user_from_app['telegram_id']
            if existing_tg and existing_tg != telegram_id:
                await message.answer(
                    "Этот аккаунт уже привязан к другому Telegram.\n"
                    "Если это ошибка, обратитесь в поддержку."
                )
                return

            success = link_telegram_to_user_by_id(user_id_from_app, telegram_id)
            if success:
                username = user_from_app['username'] or message.from_user.first_name
                await message.answer(
                    f"Аккаунт {username} успешно привязан!",
                    reply_markup=main_keyboard(),
                )
            else:
                await message.answer(
                    "Аккаунт уже привязан к другому Telegram.\n"
                    "Если это ошибка, обратитесь в поддержку."
                )
        else:
            await message.answer(
                "Пользователь не найден.\n"
                "Пожалуйста, сначала зарегистрируйтесь в приложении FinControl.\n"
                "Или отправьте номер телефона для регистрации:",
                reply_markup=phone_keyboard()
            )
        return

    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n"
        "Я — FinControl, ваш финансовый помощник.\n"
        "У вас есть два варианта:\n"
        "1. Если уже есть аккаунт в приложении — используйте ссылку из настроек\n"
        "2. Или отправьте номер телефона для быстрой регистрации\n"
        "Отправьте номер телефона:",
        reply_markup=phone_keyboard()
    )


@router.message(F.contact)
async def handle_contact(message: Message):
    phone = message.contact.phone_number
    telegram_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name

    try:
        user = get_user_by_telegram_id(telegram_id)

        if user:
            update_user_phone(telegram_id, phone)
            await message.answer(
                f"С возвращением, {first_name}!\nВаши данные обновлены.",
                reply_markup=main_keyboard(),
            )
        else:
            create_user(telegram_id, username, phone)
            await message.answer(
                f"Добро пожаловать, {first_name}!\nВы успешно зарегистрированы!",
                reply_markup=main_keyboard(),
            )

    except Exception as e:
        await message.answer(
            f"Произошла ошибка: {str(e)}\nПопробуйте позже или обратитесь в поддержку.",
            reply_markup=ReplyKeyboardRemove()
        )
