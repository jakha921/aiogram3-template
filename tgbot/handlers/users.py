from aiogram import types, Router, F
from loguru import logger

from tgbot.keyboards.reply import phone_number_kb
from tgbot.states import GetPhone

router = Router(name=__name__)


async def user_start(msg: types.Message):
    logger.info(f"User {msg.from_user.id} started the bot")
    await msg.answer("Hello! I'm echo bot!")


async def user_echo(msg: types.Message):
    logger.info(f"User {msg.from_user.id} send {msg.text}")
    await msg.answer(msg.text)


async def user_phone(msg: types.Message):
    logger.info(f"User {msg.from_user.id} send phone number")
    await msg.answer("You send phone number!", reply_markup=await phone_number_kb())

    # set state for phone number
    await GetPhone.phone.set()


# register handlers
def register_users():
    router.message.register(
        user_start,
        F.text == "/start",
    )
    router.message.register(
        user_echo,
        F.text
    )
    router.message.register(
        user_phone,
        F.text == "/phone"
    )
    router.message.register(
        user_phone,
        F.text == "📞Send phone number"
    )
    router.message.register(
        user_phone,
        F.contact,

    )

    return router
