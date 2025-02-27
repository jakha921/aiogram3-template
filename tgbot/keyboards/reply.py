from aiogram.types import ReplyKeyboardMarkup, KeyboardButton


async def phone_number_kb():
    """Back keyboard"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📞Send phone number", request_contact=True)],
        ],
        resize_keyboard=True,
    )
    return keyboard
