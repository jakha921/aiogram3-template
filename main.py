import asyncio

from aiogram import Bot, Dispatcher, types, F

TOKEN = "6275417487:AAEjFpxjnEMAMHfOlXHAH9Rg-ajNji8Rki8"


async def echo(msg: types.Message, bot: Bot):
    await bot.send_message(
        chat_id=msg.chat.id,
        text=msg.text
    )


async def main():
    bot = Bot(token=TOKEN)
    dp = Dispatcher()
    dp.message.register(
        echo,
        F.text
    )

    await dp.start_polling(bot)

    await bot.session.close()


asyncio.run(main())
