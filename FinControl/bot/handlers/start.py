from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardRemove
from aiogram.filters import Command

from bot.keyboards.reply import phone_keyboard
from bot.database import get_connection

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n"
        "Я - FinControl, ваш финансовый помощник\n\n"
        "Для начала работы мне нужен ваш номер телефона\n",
        reply_markup = phone_keyboard()
    )

# получение номера и его вненсение в бд
@router.message(F.contact)
async def handle_contact(message: Message):
    phone = message.contact.phone_number
    telegram_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name or "Пользователь"

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "SELECT id FROM users WHERE telegram_id = ?",
            (telegram_id,)
        )
        existing_user = cursor.fetchone()

        # уже есть в бд
        if existing_user:
            cursor.execute(
                "UPDATE users SET phone = ? WHERE telegram_id = ?",
                (phone, telegram_id)
            )
            conn.commit()

            await message.answer(
                f"С возвращением, {first_name}!\n"
                "Рады снова вас видеть!",
                reply_markup = ReplyKeyboardRemove()
            )

        # новый пользователь
        else:
            cursor.execute(
                "INSERT INTO users (telegram_id, username, phone) VALUES (?, ?, ?)",
                (telegram_id, username, phone)
            )
            conn.commit()

            await message.answer(
                f"Добро пожаловать, {first_name}!\n"
                "Вы успешно зарегистрированы!",
                reply_markup=ReplyKeyboardRemove()
            )

    except Exception as e:
        await message.answer(
            f"Произошла ошибка: {e}\n"
            f"Попробуй позже",
            reply_markup=ReplyKeyboardRemove()
        )

    finally:
        conn.close()