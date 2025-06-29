import asyncio
import os

from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommandScopeDefault
from loguru import logger

from tgbot.config import load_config
from tgbot.handlers.admin import register_admin
from tgbot.handlers.group import register_group
from tgbot.handlers.users import register_users
from tgbot.middlewares.db import DbMiddleware
from tgbot.middlewares.throttling import ThrottlingMiddleware
from tgbot.services.database import create_db_session

config = load_config(".env")

bot = Bot(token=config.tg_bot.token, default=DefaultBotProperties(parse_mode='HTML'))
dp = Dispatcher(storage=MemoryStorage())


def init_logger():
    """Logger initializer"""
    os.makedirs("logs", exist_ok=True)

    logger.add(
        sink="logs/bot.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{file}:{line} {message}",
        rotation="30 day",
        retention="90 days",
        compression="zip",
        backtrace=True,
        diagnose=True,
        enqueue=True,
        catch=True,
        level="DEBUG",
    )

    logger.success("Logger initialized")


def register_all_middlewares(dp: Dispatcher):
    """Register all middlewares"""
    dp.update.middleware(DbMiddleware())
    dp.message.middleware(ThrottlingMiddleware(limit=1.0)) # 1 message per second
    # dp.message.middleware(DbMiddleware())


def register_all_filters(dp: Dispatcher):
    """Register all filters"""
    # dp.filters_factory.bind(role.AdminFilter)
    # dp.filters_factory.bind(reply_kb.CloseBtn)
    pass


def register_all_handlers(dp: Dispatcher):
    """Register all handlers"""
    dp.include_router(register_admin())
    dp.include_router(register_group())
    dp.include_router(register_users())


async def set_bot_commands(bot: Bot):
    """Initialize bot commands for bot to preview them when typing slash \"/\""""
    commands = [
        types.BotCommand(command="/start", description="Для начала работы с ботом"),
        types.BotCommand(command="/admin", description="Админ панель"),
        types.BotCommand(command="/stats", description="Статистика пользователей"),
    ]
    await bot.set_my_commands(commands, scope=BotCommandScopeDefault())


async def on_startup():
    """Startup function"""
    init_logger()
    logger.success("Starting the bot...")

    # Adding config and db session to bot object
    bot.config = config
    bot.db = await create_db_session(config)

    register_all_middlewares(dp)
    # register_all_filters(dp)
    register_all_handlers(dp)

    await set_bot_commands(bot)

    # Notify admin
    for admin_id in config.tg_bot.admins_id:
        try:
            await bot.send_message(admin_id, "Bot is started")
        except Exception as e:
            logger.error(f"Error while sending message to admin {admin_id}: {e}")

    # Show log message
    logger.success("Bot started")


async def on_shutdown():
    """Shutdown function"""
    logger.success("Shutting down the bot...")

    # notify admin
    # for admin_id in config.tg_bot.admins_id:
    #     try:
    #         await bot.send_message(admin_id, "Bot is stopped")
    #     except Exception as e:
    #         logger.error(f"Error while sending message to admin {admin_id}: {e}")

    # close all connections
    await dp.storage.close()
    await bot.session.close()

    # show log message
    logger.success("Bot stopped")


async def main():
    """Main function"""
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    await dp.start_polling(
        bot,
        skip_updates=config.tg_bot.skip_updates
    )


if __name__ == "__main__":
    asyncio.run(main())
