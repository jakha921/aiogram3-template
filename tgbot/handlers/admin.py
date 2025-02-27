from typing import Any

from aiogram import types, Router
from aiogram.filters import Command
from loguru import logger

from tgbot.filters.admin import AdminFilter
from tgbot.models.models import TGUser
from tgbot.services.database import AsyncSession

router = Router(name=__name__)


async def admin_start(msg: types.Message):
    logger.info(f"Admin {msg.from_user.id} started the bot")
    await msg.answer("Hi my dear admin!")


async def admin_get_user_count(msg: types.Message):
    logger.info(f"Admin {msg.from_user.id} requested user count")
    users_count = await TGUser.get_users_count(msg.bot.db)
    await msg.answer(f"Total users: {users_count}")


# register handlers
def register_admin():
    router.message.register(
        admin_start,
        Command("start"),
        AdminFilter()
    )
    router.message.register(
        admin_get_user_count,
        Command("stats"),
        AdminFilter()
    )

    return router
