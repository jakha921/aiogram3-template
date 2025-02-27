# admin filter
from aiogram import types
from aiogram.filters import Filter

from tgbot.config import load_config


class AdminFilter(Filter):
    """
    Filter for checking if message is from admin
    """

    config = load_config(".env")

    async def __call__(self, msg: types.Message):
        return msg.from_user.id in self.config.tg_bot.admins_id
