# group chat filter
from aiogram import types
from aiogram.filters import Filter


class GroupChatFilter(Filter):
    """
    Filter for checking if message is from group
    """

    async def __call__(self, message: types.Message):
        return message.chat.type in ['group', 'supergroup']
