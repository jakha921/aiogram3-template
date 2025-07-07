from typing import Any

from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from loguru import logger
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tgbot.filters.admin import AdminFilter
from tgbot.models.models import TGUser
from tgbot.services.admin_service import AdminService
from tgbot.keyboards.factory import KeyboardFactory
from tgbot.states import AdminInvoicesFilter, ReconciliationActStates
from tgbot.misc.slope_tempalte import generate_invoice_excel, generate_reconciliation_act_excel
from aiogram.types import FSInputFile
import os

router = Router(name=__name__)


async def admin_start(msg: types.Message, state: FSMContext):
    logger.info(f"Admin {msg.from_user.id} started the bot")
    await state.clear()
    await msg.answer("👋 Привет, админ! Выберите действие:", reply_markup=KeyboardFactory.admin_menu())


async def admin_get_user_count(msg: types.Message):
    logger.info(f"Admin {msg.from_user.id} requested user count")
    admin_service = AdminService(msg.bot.db)
    users_count = await admin_service.get_users_count()
    await msg.answer(f"📊 Всего пользователей: {users_count}")


async def admin_menu(call: types.CallbackQuery, state: FSMContext):
    """Показать главное админское меню"""
    logger.info(f"Admin {call.from_user.id} opened admin menu")
    await state.clear()
    await call.message.edit_text("👋 Админ панель. Выберите действие:", reply_markup=KeyboardFactory.admin_menu())


async def admin_invoices_start(call: types.CallbackQuery, state: FSMContext):
    """Начать процесс просмотра накладных - выбор года"""
    logger.info(f"Admin {call.from_user.id} started invoices flow")
    await state.set_state(AdminInvoicesFilter.year)
    await call.message.edit_text("📅 Выберите год для просмотра накладных:", reply_markup=KeyboardFactory.years_selection())


async def admin_year_selected(call: types.CallbackQuery, state: FSMContext):
    """Обработка выбора года"""
    year = call.data.split('_')[-1]
    await state.update_data(selected_year=year)
    await state.set_state(AdminInvoicesFilter.month)
    
    logger.info(f"Admin {call.from_user.id} selected year: {year}")
    await call.message.edit_text(f"📅 Выбран год: {year}\n\nТеперь выберите месяц:", 
                                reply_markup=KeyboardFactory.months_selection())


async def admin_month_selected(call: types.CallbackQuery, state: FSMContext):
    """Обработка выбора месяца и показа списка накладных"""
    month = call.data.split('_')[-1]
    data = await state.get_data()
    year = data.get('selected_year')
    
    await state.update_data(selected_month=month)
    await state.set_state(AdminInvoicesFilter.invoices_list)
    
    logger.info(f"Admin {call.from_user.id} selected month: {month} for year: {year}")
    
    # Показываем загрузку
    await call.message.edit_text("🔄 Загружаем накладные...")
    
    try:
        admin_service = AdminService(call.bot.db)
        
        # Получаем накладные за выбранный период (оптимизированная версия)
        filtered_invoices = await admin_service.get_invoices_by_period(int(year), int(month))
        
        await state.update_data(filtered_invoices=filtered_invoices, current_page=0)
        
        if not filtered_invoices:
            await call.message.edit_text(
                f"❌ За {month}/{year} накладные не найдены",
                reply_markup=KeyboardFactory.months_selection()
            )
            return
        
        # Формируем текст с общей информацией
        header_text = admin_service.format_invoice_summary(filtered_invoices, int(year), int(month))
        
        await call.message.edit_text(
            header_text,
            reply_markup=KeyboardFactory.invoices_list(filtered_invoices, page=0)
        )
        
    except Exception as e:
        logger.error(f"Error loading invoices: {e}")
        await call.message.edit_text(
            "❌ Ошибка при загрузке накладных",
            reply_markup=KeyboardFactory.months_selection()
        )


async def admin_invoice_details(call: types.CallbackQuery, state: FSMContext):
    """Показать детали конкретной накладной"""
    sales_id = int(call.data.split('_')[-1])
    
    logger.info(f"Admin {call.from_user.id} requested details for invoice: {sales_id}")
    
    # Показываем загрузку
    await call.message.edit_text("🔄 Загружаем детали накладной...")
    
    try:
        admin_service = AdminService(call.bot.db)
        
        # Получаем детали накладной
        details = await admin_service.get_invoice_details(sales_id)
        
        if not details:
            await call.message.edit_text(
                "❌ Детали накладной не найдены",
                reply_markup=KeyboardFactory.invoice_details(sales_id)
            )
            return
        
        # Формируем детальный текст накладной
        full_text = admin_service.format_invoice_details(details, sales_id)
        
        await call.message.edit_text(
            full_text,
            reply_markup=KeyboardFactory.invoice_details(sales_id)
        )
        
    except Exception as e:
        logger.error(f"Error loading invoice details: {e}")
        await call.message.edit_text(
            "❌ Ошибка при загрузке деталей накладной",
            reply_markup=KeyboardFactory.invoice_details(0)
        )


async def admin_back_to_invoices_list(call: types.CallbackQuery, state: FSMContext):
    """Вернуться к списку накладных"""
    data = await state.get_data()
    filtered_invoices = data.get('filtered_invoices', [])
    current_page = data.get('current_page', 0)
    year = data.get('selected_year')
    month = data.get('selected_month')
    
    if not filtered_invoices:
        await call.message.edit_text("❌ Список накладных пуст", reply_markup=KeyboardFactory.months_selection())
        return
    
    admin_service = AdminService(call.bot.db)
    header_text = admin_service.format_invoice_summary(filtered_invoices, int(year), int(month))
    
    await call.message.edit_text(
        header_text,
        reply_markup=KeyboardFactory.invoices_list(filtered_invoices, page=current_page)
    )


async def admin_page_navigation(call: types.CallbackQuery, state: FSMContext):
    """Навигация по страницам списка накладных"""
    page = int(call.data.split('_')[-1])
    data = await state.get_data()
    filtered_invoices = data.get('filtered_invoices', [])
    year = data.get('selected_year')
    month = data.get('selected_month')
    
    await state.update_data(current_page=page)
    
    admin_service = AdminService(call.bot.db)
    header_text = admin_service.format_invoice_summary(filtered_invoices, int(year), int(month))
    
    await call.message.edit_text(
        header_text,
        reply_markup=KeyboardFactory.invoices_list(filtered_invoices, page=page)
    )


async def admin_stats(call: types.CallbackQuery, state: FSMContext):
    """Показать статистику"""
    logger.info(f"Admin {call.from_user.id} requested stats")
    await state.clear()
    
    try:
        admin_service = AdminService(call.bot.db)
        users_count = await admin_service.get_users_count()
        
        stats_text = (
            f"📊 <b>Статистика бота</b>\n\n"
            f"👥 Всего пользователей: <b>{users_count}</b>\n"
            f"🤖 Бот работает исправно\n"
            f"📦 Функции: накладные, регистрация"
        )
        
        await call.message.edit_text(stats_text, reply_markup=KeyboardFactory.admin_menu())
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        await call.message.edit_text(
            "❌ Ошибка при получении статистики",
            reply_markup=KeyboardFactory.admin_menu()
        )


async def admin_download_invoice(call: types.CallbackQuery, state: FSMContext):
    """Скачать накладную в Excel формате"""
    sales_id = int(call.data.split('_')[-1])
    
    logger.info(f"Admin {call.from_user.id} downloading invoice: {sales_id}")
    
    # Показываем загрузку
    await call.message.edit_text("📊 Генерируем Excel файл...")
    
    try:
        admin_service = AdminService(call.bot.db)
        
        # Получаем детали накладной
        details = await admin_service.get_invoice_details(sales_id)
        
        if not details:
            await call.message.edit_text(
                "❌ Накладная не найдена",
                reply_markup=KeyboardFactory.invoice_details(sales_id)
            )
            return
        
        # Преобразуем данные для функции генерации Excel
        excel_data = []
        for item in details:
            excel_data.append((
                item['Магазин/Склад'],      # company
                item['Код товара'],         # code  
                item['Наименование'],       # name
                item['Дата/Время'],         # date
                'Продажа',                  # operation
                item['Количество'],         # quantity
                item['Цена'],              # price
                item['Сумма'],             # amount
                'Продано'                  # status
            ))
        
        # Генерируем Excel файл
        excel_path = await generate_invoice_excel(
            invoice_data=excel_data, 
            invoice_number=f"ADM_{sales_id}"
        )
        
        # Отправляем файл
        excel_file = FSInputFile(excel_path)
        await call.message.answer_document(
            excel_file,
            caption=f"📄 Накладная #{sales_id} готова для скачивания"
        )
        
        # Удаляем временный файл
        if os.path.exists(excel_path):
            os.remove(excel_path)
        
        # Возвращаем к просмотру накладной
        await call.message.edit_text(
            "✅ Накладная успешно отправлена!",
            reply_markup=KeyboardFactory.invoice_details(sales_id)
        )
        
    except Exception as e:
        logger.error(f"Error generating invoice Excel: {e}")
        await call.message.edit_text(
            "❌ Ошибка при генерации накладной",
            reply_markup=KeyboardFactory.invoice_details(sales_id)
        )


async def admin_reconciliation_menu(call: types.CallbackQuery, state: FSMContext):
    await state.set_state(ReconciliationActStates.year)
    await call.message.edit_text(
        "📅 Выберите год для акта сверки:",
        reply_markup=KeyboardFactory.years_selection(prefix="recon_year_", back_callback="btn_admin_menu")
    )


async def admin_reconciliation_year(call: types.CallbackQuery, state: FSMContext):
    year = call.data.split('recon_year_')[-1]
    await state.update_data(recon_year=year)
    await state.set_state(ReconciliationActStates.month)
    await call.message.edit_text(
        f"📅 Год: {year}\nТеперь выберите месяц:",
        reply_markup=KeyboardFactory.months_selection(prefix="recon_month_", back_callback="btn_admin_reconciliation_menu")
    )


async def admin_reconciliation_month(call: types.CallbackQuery, state: FSMContext):
    month = call.data.split('recon_month_')[-1]
    data = await state.get_data()
    year = int(data.get('recon_year'))
    await state.update_data(recon_month=month, customers_page=0)
    await state.set_state(ReconciliationActStates.confirm)
    admin_service = AdminService(call.bot.db)
    customers = await admin_service.get_customers_by_period(year, int(month))
    if not customers:
        await call.message.edit_text(
            f"❌ Нет покупателей за {month}/{year}",
            reply_markup=KeyboardFactory.months_selection(prefix="recon_month_", back_callback="btn_admin_reconciliation_menu")
        )
        return
    header = f"👥 <b>Покупатели за {month}/{year}</b>\n\nНайдено: {len(customers)} покупателей\nВыберите покупателя для акта сверки:"
    await call.message.edit_text(
        header,
        reply_markup=KeyboardFactory.reconciliation_customers_list(customers, year, int(month), page=0),
        parse_mode="HTML"
    )


async def admin_reconciliation_customers_page(call: types.CallbackQuery, state: FSMContext):
    _, _, _, year, month, page = call.data.split('_')
    year, month, page = int(year), int(month), int(page)
    admin_service = AdminService(call.bot.db)
    customers = await admin_service.get_customers_by_period(year, month)
    header = f"👥 <b>Покупатели за {month:02d}.{year}</b>\n\nНайдено: {len(customers)} покупателей\nВыберите покупателя для акта сверки:"
    await call.message.edit_text(
        header,
        reply_markup=KeyboardFactory.reconciliation_customers_list(customers, year, month, page=page),
        parse_mode="HTML"
    )


async def admin_reconciliation_customer(call: types.CallbackQuery, state: FSMContext):
    """Показать акт сверки для выбранного покупателя (оптимизировано)"""
    _, _, year, month, phone = call.data.split("_", 4)
    year, month = int(year), int(month)
    admin_service = AdminService(call.bot.db)
    summary = await admin_service.get_reconciliation_data(phone, year, month)
    if not summary:
        await call.message.edit_text(
            "❌ Нет данных для акта сверки по этому покупателю",
            reply_markup=KeyboardFactory.years_selection(prefix="recon_year_", back_callback="btn_admin_menu")
        )
        return
    customers = await admin_service.get_customers_by_period(year, month)
    customer = next((c for c in customers if c['phone'] == phone), None)
    customer_name = customer['name'] if customer else phone
    # Фильтрация по периоду
    filtered_summary = admin_service.filter_reconciliation_data_by_period(summary, year, month)
    # Формируем текст (передаем телефон для красивого UX)
    text = admin_service.format_reconciliation_text(filtered_summary, customer_name, year, month, customer_phone=phone)
    # Клавиатура
    kb = KeyboardFactory.reconciliation_excel_download_kb(year, month, phone)
    await call.message.edit_text(text, reply_markup=kb, parse_mode="HTML")


async def admin_reconciliation_download_excel(call: types.CallbackQuery, state: FSMContext):
    """Скачать Excel файл акта сверки (оптимизировано)"""
    _, _, _, year, month, phone = call.data.split("_", 5)
    year, month = int(year), int(month)
    await call.message.edit_text("📄 Генерируем Excel файл акта сверки...")
    try:
        admin_service = AdminService(call.bot.db)
        summary = await admin_service.get_reconciliation_data(phone, year, month)
        customers = await admin_service.get_customers_by_period(year, month)
        customer = next((c for c in customers if c['phone'] == phone), None)
        customer_name = customer['name'] if customer else phone
        # Фильтрация по периоду
        filtered_summary = admin_service.filter_reconciliation_data_by_period(summary, year, month)
        # Параметры для Excel
        params = admin_service.get_reconciliation_excel_params(customer_name, year, month, filtered_summary)
        # Генерируем Excel файл
        file_path = await generate_reconciliation_act_excel(
            act_data=filtered_summary,
            **params
        )
        excel_file = FSInputFile(file_path)
        await call.message.answer_document(
            excel_file, 
            caption=f"📄 Акт сверки за {params['period_start']} - {params['period_end']} для {customer_name}"
        )
        if os.path.exists(file_path):
            os.remove(file_path)
        await call.answer("✅ Акт сверки успешно отправлен!", show_alert=True)
    except Exception as e:
        logger.error(f"Error generating reconciliation Excel: {e}")
        await call.message.edit_text(f"❌ Ошибка при генерации акта сверки: {e}")


async def admin_reconciliation_back_customers(call: types.CallbackQuery, state: FSMContext):
    """Вернуться к списку покупателей"""
    _, _, _, year, month = call.data.split("_", 4)
    year, month = int(year), int(month)
    
    admin_service = AdminService(call.bot.db)
    customers = await admin_service.get_customers_by_period(year, month)
    
    await call.message.edit_text(
        f"📅 Год: {year}, Месяц: {month}\nВыберите покупателя для акта сверки:",
        reply_markup=KeyboardFactory.act_customers(customers, year, month)
    )


# Стартовый хендлер для акта сверки
@router.message(Command("act_sverki"), AdminFilter())
async def act_sverki_start(message: types.Message):
    admin_service = AdminService(message.bot.db)
    years = await admin_service.get_sales_years()
    await message.answer("Выберите год:", reply_markup=KeyboardFactory.act_years(years))

# Хендлер для выбора года
@router.callback_query(lambda c: c.data.startswith("act_year_"), AdminFilter())
async def act_sverki_choose_year(call: types.CallbackQuery, state: FSMContext):
    year = int(call.data.split("_")[-1])
    admin_service = AdminService(call.bot.db)
    months = await admin_service.get_sales_months(year)
    await call.message.edit_text(f"Год: {year}\nВыберите месяц:", reply_markup=KeyboardFactory.act_months(months, year))
    await state.update_data(act_year=year)

# Хендлер для выбора месяца
@router.callback_query(lambda c: c.data.startswith("act_month_"), AdminFilter())
async def act_sverki_choose_month(call: types.CallbackQuery, state: FSMContext):
    _, _, year, month = call.data.split("_")
    year, month = int(year), int(month)
    admin_service = AdminService(call.bot.db)
    customers = await admin_service.get_customers_by_period(year, month)
    await call.message.edit_text(f"Год: {year}, Месяц: {month}\nВыберите покупателя:", reply_markup=KeyboardFactory.act_customers(customers, year, month))
    await state.update_data(act_month=month)

# Хендлер для выбора покупателя и показа акта сверки
@router.callback_query(lambda c: c.data.startswith("act_customer_"), AdminFilter())
async def act_sverki_show(call: types.CallbackQuery, state: FSMContext):
    _, _, year, month, phone = call.data.split("_", 4)
    year, month = int(year), int(month)
    admin_service = AdminService(call.bot.db)
    summary = await admin_service.get_reconciliation_data(phone, year, month)
    customers = await admin_service.get_customers_by_period(year, month)
    customer = next((c for c in customers if c['phone'] == phone), None)
    customer_name = customer['name'] if customer else phone
    text = admin_service.format_reconciliation_text(summary, customer_name, year, month, customer_phone=phone)
    await call.message.edit_text(text, reply_markup=KeyboardFactory.act_download(year, month, phone), parse_mode="HTML")

# Хендлер для скачивания акта сверки
@router.callback_query(lambda c: c.data.startswith("act_download_"), AdminFilter())
async def act_sverki_download(call: types.CallbackQuery, state: FSMContext):
    _, _, year, month, phone = call.data.split("_", 4)
    year, month = int(year), int(month)
    admin_service = AdminService(call.bot.db)
    summary = await admin_service.get_reconciliation_data(phone, year, month)
    customers = await admin_service.get_customers_by_period(year, month)
    customer = next((c for c in customers if c['phone'] == phone), None)
    customer_name = customer['name'] if customer else phone
    
    # Фильтруем summary по выбранному периоду
    filtered_summary = [row for row in summary if hasattr(row['Дата'], 'year') and row['Дата'].year == year and row['Дата'].month == month]
    
    # Параметры для генерации Excel
    company1 = "AVTOLIDER"
    company2 = customer_name
    period_start = f"01.{month:02d}.{year}"
    period_end = f"31.{month:02d}.{year}"
    saldo_start = 0.0
    saldo_end = filtered_summary[-1]['Долг'] if filtered_summary else 0.0
    
    file_path = await generate_reconciliation_act_excel(
        act_data=filtered_summary,
        company1=company1,
        company2=company2,
        period_start=period_start,
        period_end=period_end,
        saldo_start=saldo_start,
        saldo_end=saldo_end
    )
    try:
        await call.message.answer_document(FSInputFile(file_path), caption=f"Акт сверки за {period_start} - {period_end} для {customer_name}")
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
    await call.answer("Акт сверки сформирован и отправлен.", show_alert=True)


# register handlers
def register_admin():
    router.message.register(
        admin_start,
        Command("admin"),
        AdminFilter()
    )
    router.message.register(
        admin_get_user_count,
        Command("stats"),
        AdminFilter()
    )
    
    # Admin callback handlers
    router.callback_query.register(
        admin_menu,
        F.data == "btn_admin_menu",
        AdminFilter()
    )
    router.callback_query.register(
        admin_invoices_start,
        F.data == "btn_admin_invoices",
        AdminFilter()
    )
    router.callback_query.register(
        admin_year_selected,
        F.data.startswith("btn_admin_year_"),
        AdminFilter()
    )
    router.callback_query.register(
        admin_month_selected,
        F.data.startswith("btn_admin_month_"),
        AdminFilter()
    )
    router.callback_query.register(
        admin_invoice_details,
        F.data.startswith("btn_admin_invoice_details_"),
        AdminFilter()
    )
    router.callback_query.register(
        admin_back_to_invoices_list,
        F.data == "btn_admin_back_to_list",
        AdminFilter()
    )
    router.callback_query.register(
        admin_page_navigation,
        F.data.startswith("btn_admin_page_"),
        AdminFilter()
    )
    router.callback_query.register(
        admin_stats,
        F.data == "btn_admin_stats",
        AdminFilter()
    )
    router.callback_query.register(
        admin_download_invoice,
        F.data.startswith("btn_admin_download_"),
        AdminFilter()
    )
    router.callback_query.register(
        admin_reconciliation_menu,
        F.data == "btn_admin_reconciliation_menu",
        AdminFilter()
    )
    router.callback_query.register(
        admin_reconciliation_year,
        F.data.startswith("recon_year_"),
        AdminFilter()
    )
    router.callback_query.register(
        admin_reconciliation_month,
        F.data.startswith("recon_month_"),
        AdminFilter()
    )
    router.callback_query.register(
        admin_reconciliation_customer,
        F.data.startswith("act_customer_"),
        AdminFilter()
    )
    router.callback_query.register(
        admin_reconciliation_download_excel,
        F.data.startswith("recon_download_excel_"),
        AdminFilter()
    )
    router.callback_query.register(
        admin_reconciliation_back_customers,
        F.data.startswith("recon_back_customers_"),
        AdminFilter()
    )
    router.callback_query.register(
        admin_reconciliation_customers_page,
        F.data.startswith("recon_customers_page_"),
        AdminFilter()
    )

    return router
