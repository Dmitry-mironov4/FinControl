# handlers/start.py
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import Command

from bot.keyboards.reply import phone_keyboard
from bot.keyboards.inline import main_menu_keyboard
from fincontrolapp.db_queries import get_user_by_telegram_id, create_user, update_user_phone, link_telegram_to_user_by_id, get_user_by_id

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    # Обработчик команды /start
    args = message.text.split()
    deep_link_user_id = args[1] if len(args) > 1 else None

    telegram_id = message.from_user.id
    user = get_user_by_telegram_id(telegram_id)

    # Случай 1: Пользователь уже привязан
    if user:
        await message.answer(
            f"👋 С возвращением, {user['username'] or message.from_user.first_name}!",
            reply_markup=main_menu_keyboard()
        )
        return

    # Случай 2: Привязка через deep link из приложения
    if deep_link_user_id and deep_link_user_id.isdigit():
        user_id_from_app = int(deep_link_user_id)

        # Проверяем, существует ли пользователь с таким ID
        user_from_app = get_user_by_id(user_id_from_app)

        if user_from_app:
            # Привязываем telegram_id
            success = link_telegram_to_user_by_id(user_id_from_app, telegram_id)

            if success:
                await message.answer(
                    "Аккаунт успешно привязан!\n\n",
                    reply_markup=main_menu_keyboard()
                )
            else:
                await message.answer(
                    "Аккаунт уже привязан к другому Telegram.\n"
                    "Если это ошибка, обратитесь в поддержку."
                )
        else:
            await message.answer(
                "Пользователь не найден.\n"
                "Пожалуйста, для начала зарегистрируйтесь в приложении FinControl.\n"
                "Или отправьте свой номер телефона для регистрации:",
                reply_markup=phone_keyboard()
            )
        return

    # Случай 3: Новый пользователь без привязки
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n"
        "Я - FinControl, ваш финансовый помощник.\n"
        "У вас есть два варианта:\n"
        "1. Если уже есть аккаунт в приложении — используйте ссылку из настроек\n"
        "2. Или отправьте номер телефона для быстрой регистрации\n"
        "Отправьте номер телефона:",
        reply_markup=phone_keyboard()
    )


@router.message(F.contact)
async def handle_contact(message: Message):
    # Получение номера телефона и регистрация
    phone = message.contact.phone_number
    telegram_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name

    try:
        user = get_user_by_telegram_id(telegram_id)

        if user:
            # Обновляем телефон у существующего пользователя
            update_user_phone(telegram_id, phone)
            await message.answer(
                f"С возвращением, {first_name}!\n"
                "Ваши данные обновлены.",
                reply_markup=main_menu_keyboard()
            )
        else:
            # Создаем нового пользователя с telegram_id
            create_user(telegram_id, username, phone)
            await message.answer(
                f"Добро пожаловать, {first_name}!\n"
                "Вы успешно зарегистрированы!",
                reply_markup=main_menu_keyboard()
            )

    except Exception as e:
        await message.answer(
            f"Произошла ошибка: {str(e)}\n"
            "Попробуйте позже или обратитесь в поддержку.",
            reply_markup=ReplyKeyboardRemove()
        )