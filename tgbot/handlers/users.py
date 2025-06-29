import re
from pprint import pprint
import os

from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
from loguru import logger

from tgbot.keyboards.inline import user_menu_kb_inline, month_kb_inline
from tgbot.keyboards.reply import phone_number_kb
from tgbot.models.models import TGUser
from tgbot.states import GetPhone
from tgbot.misc.slope_tempalte import generate_invoice_excel

router = Router(name=__name__)


async def user_start(msg: types.Message, state: FSMContext):
    logger.info(f"User {msg.from_user.id} started the bot")

    # state clear
    if await state.get_state():
        await state.clear()

    user: TGUser = await TGUser.get_user(msg.bot.db, msg.from_user.id)
    print('user', user)
    print('user', user.phone)

    # check if user has phone number
    if not user.phone:
        await state.set_state(GetPhone.phone)
        await msg.answer("📞 Чтобы продолжить, отправьте свой номер телефона\n\n"
                         "<b>Пример: 998901234567</b>",
                         )
    else:
        await msg.answer(f"Добро пожаловать, {msg.from_user.full_name}!", reply_markup=await user_menu_kb_inline())


async def get_user_phone(msg: types.Message, state: FSMContext):
    logger.info(f"User {msg.from_user.id} send phone number")

    user_phone = msg.text
    print('user_phone', user_phone)

    # validate phone number
    if not user_phone:
        await msg.answer("Если вы хотите продолжить, отправьте свой номер телефона\n\n"
                         "<b>Пример: 998901234567</b>",
                         reply_markup=await phone_number_kb())
        return

    if user_phone.isdigit() and len(user_phone) == 9:
        await msg.answer("Номер телефона должен начинаться с кода страны\nПример: 998901234567")

    # set in standard format
    if re.match(r'^\+998\d{9}$', user_phone):
        # remove plus
        user_phone = user_phone[1:]
    elif re.match(r'^998\d{9}$', user_phone):
        user_phone = user_phone
    else:
        await msg.answer("Неверный формат номера телефона\n\nПример: 998901234567")
        return

    # clear state
    await state.clear()

    # remove btn phone number
    await msg.delete()
    # delete previous message
    await msg.bot.delete_message(msg.chat.id, msg.message_id - 1)

    # save phone number to db
    if user_phone:
        user = await TGUser.update_user(
            msg.bot.db,
            msg.from_user.id,
            phone=user_phone
        )
        await msg.answer(f"Ваш номер телефона сохранен: {user_phone}")

        await msg.answer(f"Добро пожаловать, {msg.from_user.full_name}!", reply_markup=await user_menu_kb_inline())
    else:
        await msg.answer("Ошибка сохранения номера телефона\nПопробуйте еще раз для этого напишите /start")


async def update_user_phone(call: types.CallbackQuery, state: FSMContext):
    logger.info(f"User {call.from_user.id} send {call.data}")

    await state.set_state(GetPhone.phone)
    await call.message.edit_text("📞 Чтобы продолжить, отправьте свой номер телефона\n\n"
                                 "<b>Пример: 998901234567</b>",
                                 )


async def get_contact(call: types.CallbackQuery):
    logger.info(f"User {call.from_user.id} send {call.data}")
    contact_info = (
        "🏢 Название компании: Пример Компании\n"
        "📍 Адрес: Навои, Узбекистан\n"
        "📞 Телефон: +998930850955\n"
        "🌐 Веб-сайт: www.example.com\n"
        "📧 Электронная почта: info@example.com\n"
        "📝 Описание: Мы являемся ведущей компанией в отрасли, предоставляющей высококачественные услуги и продукты."
    )
    await call.message.edit_text(contact_info)
    await call.message.answer("🏠 Главное меню", reply_markup=await user_menu_kb_inline())


async def get_months_btn(call: types.CallbackQuery):
    logger.info(f"User {call.from_user.id} send {call.data}")
    await call.message.edit_text("Выберите месяц 👇", reply_markup=await month_kb_inline())


async def get_main_menu(call: types.CallbackQuery):
    logger.info(f"User {call.from_user.id} send {call.data}")
    await call.message.edit_text("🏠 Главное меню", reply_markup=await user_menu_kb_inline())

async def get_user_invoice(call: types.CallbackQuery):
    logger.info(f"User {call.from_user.id} sent {call.data}")
    month = call.data.split('_')[-2]
    month_name = call.data.split('_')[-1]
    # Подтверждаем выбор месяца
    await call.message.edit_text(
        # replave month to month name
        f"📅 <b>Вы выбрали месяц:</b> {month_name}",
    )

    # Получаем пользователя и данные по счету
    user: TGUser = await TGUser.get_user(call.bot.db, call.from_user.id)
    print('user', user.phone)
    print('month', month)
    res = await TGUser.get_user_invoice(call.bot.db, user.phone, month)
    # print('-' * 10)
    # pprint(res)

    if not res:
        await call.message.answer(
            "❗️ <b>За указанный месяц счёт не найден.</b>",
        )
    else:
        # Собираем все строки в один текст
        # lines = []
        # for shop, code, name, dt, typ, qty, price, total, status in res:
        #     qty_str = str(int(qty)) if qty.is_integer() else str(qty)
        #     price_str = f"{price:,.0f}".replace(",", " ") + " сум"
        #     total_str = f"{total:,.0f}".replace(",", " ") + " сум"
        #     lines.append(
        #         f"🏬 <b>{shop}</b>\n"
        #         f"📋 {name}\n"
        #         f"🕒 {dt.strftime('%Y-%m-%d %H:%M:%S')}\n"
        #         f"🔢 Количество: {qty_str}\n"
        #         f"💵 Цена: {price_str}\n"
        #         f"💰 Сумма: {total_str}\n"
        #         "--------------------------------"
        #     )
        # text = (
        #     f"<b>📑 Счёт за {month}:</b>\n\n" +
        #     "\n\n".join(lines)
        # )
        # await call.message.answer(text)
        
        wait = await call.message.answer(
            "📊 Генерируем Excel файл...",
            # reply_markup=await user_menu_kb_inline(),
        )
        
        # generate excel
        excel_path = await generate_invoice_excel(invoice_data=res, invoice_number=user.phone)
        print('excel_path', excel_path)

        # send excel file using FSInputFile
        excel_file = FSInputFile(excel_path)
        await call.message.answer_document(
            excel_file,
            caption=f"📄 Ваша накладная за {month_name} готова!"
        )
        # delete excel file
        if os.path.exists(excel_path):
            os.remove(excel_path)
        
        # delete message
        await wait.delete()

    # Возвращаем пользователя в главное меню
    await call.message.answer(
        "🏠 <b>Главное меню</b>",
        reply_markup=await user_menu_kb_inline(),
    )


# async def get_invoice_excel(msg: types.Message):
#     logger.info(f"User {msg.from_user.id} sent {msg.text}")
#     await msg.answer("🔍 Проверяем данные...")

#     try:
#         # get user
#         user: TGUser = await TGUser.get_user(msg.bot.db, msg.from_user.id)
#         print('user', user.phone)

#         # get invoice
#         res = await TGUser.get_user_invoice(msg.bot.db, user.phone, '12')
#         print('-' * 10)
#         pprint(res)

#         if not res:
#             await msg.answer("❌ Накладные за декабрь не найдены")
#             return

#         await msg.answer("📊 Генерируем Excel файл...")

#         # generate excel
#         excel_path = await generate_invoice_excel(invoice_data=res, invoice_number=user.phone)
#         print('excel', excel_path)

#         # send excel file using FSInputFile
#         excel_file = FSInputFile(excel_path)
#         await msg.answer_document(
#             excel_file,
#             caption="📄 Ваша накладная готова!"
#         )

#         # удаляем временный файл после отправки
#         if os.path.exists(excel_path):
#             os.remove(excel_path)
            
#     except Exception as e:
#         logger.error(f"Error generating invoice: {e}")
#         await msg.answer(f"❌ Произошла ошибка при генерации накладной: {str(e)}")

# register handlers
def register_users():
    router.message.register(
        user_start,
        F.text == "/start",
    )
    # router.message.register(
    #     get_invoice_excel,
    #     F.text == '/invoice'
    # )
    router.message.register(
        get_user_phone,
        GetPhone.phone
    )
    router.callback_query.register(
        update_user_phone,
        F.data == 'btn_register'
    )
    router.callback_query.register(
        get_contact,
        F.data == 'btn_contact'
    )
    router.callback_query.register(
        get_months_btn,
        F.data == 'btn_invoices'
    )
    router.callback_query.register(
        get_main_menu,
        F.data == 'btn_main_menu'
    )
    router.callback_query.register(
        get_user_invoice,
        F.data.startswith('btn_month_')
    )

    return router
