from typing import Dict, Any

from aiogram import BaseMiddleware
from aiogram.types import Message, User, CallbackQuery

from tgbot.models.models import TGUser


class DbMiddleware(BaseMiddleware):
    """Middleware for adding user into DB if they don't exist"""

    async def __call__(self, handler, event: Message | CallbackQuery, data: Dict[str, Any]):
        """Override the __call__ method to add DB logic"""
        # Retrieve db session from the data dictionary
        db_session = event.bot.db

        if event.message:
            telegram_user: User = event.message.from_user
        elif event.callback_query:
            telegram_user: User = event.callback_query.from_user

        # Check if the user exists in the DB
        user = await TGUser.get_user(db_session=db_session, telegram_id=telegram_user.id)

        if not user:
            # If the user does not exist, add them to the DB
            await TGUser.add_user(
                db_session=db_session,
                telegram_id=telegram_user.id,
                firstname=telegram_user.first_name,
                lastname=telegram_user.last_name,
                username=telegram_user.username,
                lang_code=telegram_user.language_code,
            )
            user = await TGUser.get_user(db_session=db_session, telegram_id=telegram_user.id)

        # Add both db_session and user to the data for access in the handler
        data['db_session'] = db_session
        data['db_user'] = user

        # Now call the handler function
        return await handler(event, data)
