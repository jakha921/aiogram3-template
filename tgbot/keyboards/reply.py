from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


async def phone_number_kb():
    """Back keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📞 Отправить номер телефона", request_contact=True, one_time_keyboard=True)],
        ],
        resize_keyboard=True,
    )
    return keyboard
