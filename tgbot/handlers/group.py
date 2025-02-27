from aiogram import types, Router, F
from aiogram.filters import ChatMemberUpdatedFilter, JOIN_TRANSITION
from loguru import logger

from tgbot.filters.group import GroupChatFilter

router = Router(name=__name__)


async def group_start(msg: types.Message):
    logger.info(f"User {msg.from_user.id} started the bot in group {msg.chat.id}")
    await msg.answer(f"Hello! Dear {msg.from_user.mention_html()}!")


async def welcome_new_member(event: types.ChatMemberUpdated):
    """Handler for welcoming new members"""
    logger.info(f"New member event: {event}")
    new_member = event.new_chat_member.user
    chat = event.chat

    welcome_text = (
        f"Welcome {new_member.mention_html()} to {chat.title}!\n"
        f"Feel free to introduce yourself and join our discussions."
    )

    logger.info(f"New member {new_member.id} joined group {chat.id}")
    await event.answer(welcome_text)


# register handlers
def register_group():
    router.message.register(
        group_start,
        F.text == "hi",
        GroupChatFilter()
    )
    router.chat_member.register(
        welcome_new_member,
        ChatMemberUpdatedFilter(member_status_changed=JOIN_TRANSITION),
        GroupChatFilter()
    )

    return router
