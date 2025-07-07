import re
from pprint import pprint
import os

from aiogram import types, Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
from loguru import logger

from tgbot.keyboards.inline import user_menu_kb_inline, month_kb_inline, user_reconciliation_years_kb_inline, user_reconciliation_months_kb_inline, user_invoices_years_kb_inline, user_invoices_months_kb_inline
from tgbot.keyboards.reply import phone_number_kb
from tgbot.models.models import TGUser
from tgbot.states import GetPhone, UserReconciliationStates, UserInvoicesStates
from tgbot.misc.slope_tempalte import generate_invoice_excel, generate_reconciliation_act_excel
from tgbot.services.user_service import UserService

router = Router(name=__name__)


async def user_start(msg: types.Message, state: FSMContext):
    logger.info(f"User {msg.from_user.id} started the bot")

    # state clear
    if await state.get_state():
        await state.clear()

    user_service = UserService(msg.bot.db)
    user = await user_service.get_user_by_telegram_id(msg.from_user.id)
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
        user_service = UserService(msg.bot.db)
        user = await user_service.update_user_phone(msg.from_user.id, user_phone)
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


async def get_main_menu(call: types.CallbackQuery):
    logger.info(f"User {call.from_user.id} send {call.data}")
    await call.message.edit_text("🏠 Главное меню", reply_markup=await user_menu_kb_inline())


async def user_invoices_start(call: types.CallbackQuery, state: FSMContext):
    """Начать процесс просмотра накладных пользователя"""
    logger.info(f"User {call.from_user.id} started invoices flow")
    await state.set_state(UserInvoicesStates.year)
    await call.message.edit_text("📅 Выберите год для накладных:", reply_markup=await user_invoices_years_kb_inline())


async def user_reconciliation_start(call: types.CallbackQuery, state: FSMContext):
    """Начать процесс акта сверки пользователя"""
    logger.info(f"User {call.from_user.id} started reconciliation flow")
    await state.set_state(UserReconciliationStates.year)
    await call.message.edit_text("📅 Выберите год для акта сверки:", reply_markup=await user_reconciliation_years_kb_inline())


async def user_reconciliation_year(call: types.CallbackQuery, state: FSMContext):
    """Обработка выбора года для акта сверки пользователя"""
    year = call.data.split('_')[-1]
    await state.update_data(user_recon_year=year)
    await state.set_state(UserReconciliationStates.month)
    
    logger.info(f"User {call.from_user.id} selected year: {year}")
    await call.message.edit_text(f"📅 Выбран год: {year}\n\nТеперь выберите месяц:", 
                                reply_markup=await user_reconciliation_months_kb_inline())


async def user_reconciliation_month(call: types.CallbackQuery, state: FSMContext):
    """Обработка выбора месяца и генерация акта сверки пользователя"""
    month = call.data.split('_')[-1]
    data = await state.get_data()
    year = data.get('user_recon_year')
    
    logger.info(f"User {call.from_user.id} selected month: {month} for year: {year}")
    
    # Получаем пользователя
    user_service = UserService(call.bot.db)
    user = await user_service.get_user_by_telegram_id(call.from_user.id)
    
    if not user.phone:
        await call.message.edit_text("❌ Номер телефона не найден. Обратитесь к администратору.")
        return
    
    # Показываем загрузку
    await call.message.edit_text("🔄 Генерируем акт сверки...")
    
    try:
        # Получаем данные акта сверки для пользователя
        summary = await user_service.get_user_reconciliation(user.phone, int(year), int(month))
        
        if not summary:
            await call.message.edit_text(
                f"❌ За {month}/{year} данные для акта сверки не найдены",
                reply_markup=await user_reconciliation_months_kb_inline()
            )
            return
        
        # Формируем текст акта сверки
        header_text = user_service.format_reconciliation_summary(summary, user.phone, year, month)
        await call.message.edit_text(header_text)
        
        # Получаем название покупателя
        customer_name = await user_service.get_customer_name(user.phone)
        
        # Получаем параметры для Excel
        total_debt = sum(float(row.get('Долг', 0) or 0) for row in summary)
        excel_params = user_service.get_reconciliation_excel_params(customer_name, int(year), int(month), total_debt)
        
        # Генерируем Excel файл акта сверки
        file_path = await generate_reconciliation_act_excel(
            act_data=summary,
            **excel_params
        )
        
        # Отправляем файл
        excel_file = FSInputFile(file_path)
        await call.message.answer_document(
            excel_file,
            caption=f"📄 Ваш акт сверки за {excel_params['period_start']} - {excel_params['period_end']} готов!"
        )
        
        # Удаляем файл
        if os.path.exists(file_path):
            os.remove(file_path)
        
        # Возвращаем в главное меню
        await call.message.answer(
            "🏠 <b>Главное меню</b>",
            reply_markup=await user_menu_kb_inline(),
        )
        
    except Exception as e:
        logger.error(f"Error generating user reconciliation: {e}")
        await call.message.edit_text(
            "❌ Ошибка при генерации акта сверки",
            reply_markup=await user_reconciliation_months_kb_inline()
        )


async def user_invoices_year(call: types.CallbackQuery, state: FSMContext):
    """Обработка выбора года для накладных пользователя"""
    year = call.data.split('_')[-1]
    await state.update_data(user_invoice_year=year)
    await state.set_state(UserInvoicesStates.month)
    
    logger.info(f"User {call.from_user.id} selected year: {year}")
    await call.message.edit_text(f"📅 Выбран год: {year}\n\nТеперь выберите месяц:", 
                                reply_markup=await user_invoices_months_kb_inline())


async def user_invoices_month(call: types.CallbackQuery, state: FSMContext):
    """Обработка выбора месяца и генерация накладной пользователя"""
    month = call.data.split('_')[-1]
    data = await state.get_data()
    year = data.get('user_invoice_year')
    
    logger.info(f"User {call.from_user.id} selected month: {month} for year: {year}")
    
    # Получаем пользователя
    user_service = UserService(call.bot.db)
    user = await user_service.get_user_by_telegram_id(call.from_user.id)
    
    if not user.phone:
        await call.message.edit_text("❌ Номер телефона не найден. Обратитесь к администратору.")
        return
    
    # Подтверждаем выбор месяца
    month_names = {
        "01": "Январь", "02": "Февраль", "03": "Март", "04": "Апрель",
        "05": "Май", "06": "Июнь", "07": "Июль", "08": "Август",
        "09": "Сентябрь", "10": "Октябрь", "11": "Ноябрь", "12": "Декабрь"
    }
    month_name = month_names.get(month, month)
    
    await call.message.edit_text(
        f"📅 <b>Вы выбрали:</b> {month_name} {year}",
    )

    # Получаем данные по счету
    res = await user_service.get_user_invoice(user.phone, month)

    if not res:
        await call.message.answer(
            "❗️ <b>За указанный месяц счёт не найден.</b>",
        )
    else:
        wait = await call.message.answer(
            "📊 Генерируем Excel файл...",
        )
        
        # generate excel
        excel_path = await generate_invoice_excel(invoice_data=res, invoice_number=user.phone)
        print('excel_path', excel_path)

        # send excel file using FSInputFile
        excel_file = FSInputFile(excel_path)
        await call.message.answer_document(
            excel_file,
            caption=f"📄 Ваша накладная за {month_name} {year} готова!"
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


# register handlers
def register_users():
    router.message.register(
        user_start,
        F.text == "/start",
    )
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
        get_main_menu,
        F.data == 'btn_main_menu'
    )

    router.callback_query.register(
        user_reconciliation_start,
        F.data == 'btn_user_reconciliation'
    )
    router.callback_query.register(
        user_reconciliation_year,
        F.data.startswith('btn_user_recon_year_')
    )
    router.callback_query.register(
        user_reconciliation_month,
        F.data.startswith('btn_user_recon_month_')
    )
    router.callback_query.register(
        user_invoices_year,
        F.data.startswith('btn_user_invoice_year_')
    )
    router.callback_query.register(
        user_invoices_month,
        F.data.startswith('btn_user_invoice_month_')
    )
    router.callback_query.register(
        user_invoices_start,
        F.data == 'btn_user_invoices'
    )

    return router
