from typing import Any

from aiogram import types, Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from loguru import logger

from tgbot.filters.admin import AdminFilter
from tgbot.models.models import TGUser
from tgbot.keyboards.inline import (
    admin_menu_kb_inline, 
    admin_years_kb_inline, 
    admin_months_kb_inline,
    admin_invoices_list_kb_inline,
    admin_invoice_details_kb_inline
)
from tgbot.states import AdminInvoicesFilter
from tgbot.misc.slope_tempalte import generate_invoice_excel
from aiogram.types import FSInputFile
import os

router = Router(name=__name__)


async def admin_start(msg: types.Message, state: FSMContext):
    logger.info(f"Admin {msg.from_user.id} started the bot")
    await state.clear()
    await msg.answer("👋 Привет, админ! Выберите действие:", reply_markup=await admin_menu_kb_inline())


async def admin_get_user_count(msg: types.Message):
    logger.info(f"Admin {msg.from_user.id} requested user count")
    users_count = await TGUser.get_users_count(msg.bot.db)
    await msg.answer(f"📊 Всего пользователей: {users_count}")


async def admin_menu(call: types.CallbackQuery, state: FSMContext):
    """Показать главное админское меню"""
    logger.info(f"Admin {call.from_user.id} opened admin menu")
    await state.clear()
    await call.message.edit_text("👋 Админ панель. Выберите действие:", reply_markup=await admin_menu_kb_inline())


async def admin_invoices_start(call: types.CallbackQuery, state: FSMContext):
    """Начать процесс просмотра накладных - выбор года"""
    logger.info(f"Admin {call.from_user.id} started invoices flow")
    await state.set_state(AdminInvoicesFilter.year)
    await call.message.edit_text("📅 Выберите год для просмотра накладных:", reply_markup=await admin_years_kb_inline())


async def admin_year_selected(call: types.CallbackQuery, state: FSMContext):
    """Обработка выбора года"""
    year = call.data.split('_')[-1]
    await state.update_data(selected_year=year)
    await state.set_state(AdminInvoicesFilter.month)
    
    logger.info(f"Admin {call.from_user.id} selected year: {year}")
    await call.message.edit_text(f"📅 Выбран год: {year}\n\nТеперь выберите месяц:", 
                                reply_markup=await admin_months_kb_inline())


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
        # Получаем все накладные за выбранный период
        invoices = await TGUser.get_all_sales_invoices_summary(call.bot.db)
        
        # Фильтруем по году и месяцу
        filtered_invoices = []
        for invoice in invoices:
            invoice_date = invoice['Дата/время']
            if invoice_date.year == int(year) and invoice_date.month == int(month):
                filtered_invoices.append(invoice)
        
        await state.update_data(filtered_invoices=filtered_invoices)
        
        if not filtered_invoices:
            await call.message.edit_text(
                f"❌ За {month}/{year} накладные не найдены",
                reply_markup=await admin_months_kb_inline()
            )
            return
        
        # Формируем текст с общей информацией
        total_sum = sum(invoice['Сумма продажи'] for invoice in filtered_invoices)
        header_text = (
            f"📦 <b>Накладные за {month}/{year}</b>\n\n"
            f"📊 Найдено: {len(filtered_invoices)} накладных\n"
            f"💰 Общая сумма: {total_sum:,.0f} сум\n\n"
            f"Выберите накладную для детального просмотра:"
        )
        
        await call.message.edit_text(
            header_text,
            reply_markup=await admin_invoices_list_kb_inline(filtered_invoices)
        )
        
    except Exception as e:
        logger.error(f"Error loading invoices: {e}")
        await call.message.edit_text(
            "❌ Ошибка при загрузке накладных",
            reply_markup=await admin_months_kb_inline()
        )


async def admin_invoice_details(call: types.CallbackQuery, state: FSMContext):
    """Показать детали конкретной накладной"""
    sales_id = int(call.data.split('_')[-1])
    
    logger.info(f"Admin {call.from_user.id} requested details for invoice: {sales_id}")
    
    # Показываем загрузку
    await call.message.edit_text("🔄 Загружаем детали накладной...")
    
    try:
        # Получаем детали накладной
        details = await TGUser.get_sales_document_details(call.bot.db, sales_id)
        
        if not details:
            await call.message.edit_text(
                "❌ Детали накладной не найдены",
                reply_markup=await admin_invoice_details_kb_inline(sales_id)
            )
            return
        
        # Формируем детальный текст накладной
        first_item = details[0]
        header = (
            f"📋 <b>Накладная #{sales_id}</b>\n"
            f"🏪 Магазин: {first_item['Магазин/Склад']}\n"
            f"📅 Дата: {first_item['Дата/Время'].strftime('%d.%m.%Y %H:%M')}\n\n"
            f"<b>📦 Товары:</b>\n"
        )
        
        items_text = []
        total_sum = 0
        
        for item in details:
            item_total = item['Сумма']
            total_sum += item_total
            
            items_text.append(
                f"• <b>{item['Наименование']}</b>\n"
                f"  Код: {item['Код товара']}\n"
                f"  Кол-во: {item['Количество']}\n"
                f"  Цена: {item['Цена']:,.0f} сум\n"
                f"  Сумма: {item_total:,.0f} сум"
            )
        
        # Ограничиваем количество товаров для отображения
        if len(items_text) > 10:
            displayed_items = items_text[:10]
            displayed_items.append(f"\n... и еще {len(items_text) - 10} товаров")
        else:
            displayed_items = items_text
        
        footer = f"\n\n💰 <b>Итого: {total_sum:,.0f} сум</b>"
        
        full_text = header + "\n\n".join(displayed_items) + footer
        
        # Проверяем длину сообщения (ограничение Telegram)
        if len(full_text) > 4000:
            # Сокращаем количество товаров
            short_items = items_text[:5]
            short_items.append(f"\n... и еще {len(items_text) - 5} товаров")
            full_text = header + "\n\n".join(short_items) + footer
        
        await call.message.edit_text(
            full_text,
            reply_markup=await admin_invoice_details_kb_inline(sales_id)
        )
        
    except Exception as e:
        logger.error(f"Error loading invoice details: {e}")
        await call.message.edit_text(
            "❌ Ошибка при загрузке деталей накладной",
            reply_markup=await admin_invoice_details_kb_inline(0)
        )


async def admin_back_to_invoices_list(call: types.CallbackQuery, state: FSMContext):
    """Вернуться к списку накладных"""
    data = await state.get_data()
    filtered_invoices = data.get('filtered_invoices', [])
    year = data.get('selected_year')
    month = data.get('selected_month')
    
    if not filtered_invoices:
        await call.message.edit_text("❌ Список накладных пуст", reply_markup=await admin_months_kb_inline())
        return
    
    total_sum = sum(invoice['Сумма продажи'] for invoice in filtered_invoices)
    header_text = (
        f"📦 <b>Накладные за {month}/{year}</b>\n\n"
        f"📊 Найдено: {len(filtered_invoices)} накладных\n"
        f"💰 Общая сумма: {total_sum:,.0f} сум\n\n"
        f"Выберите накладную для детального просмотра:"
    )
    
    await call.message.edit_text(
        header_text,
        reply_markup=await admin_invoices_list_kb_inline(filtered_invoices)
    )


async def admin_stats(call: types.CallbackQuery, state: FSMContext):
    """Показать статистику"""
    logger.info(f"Admin {call.from_user.id} requested stats")
    await state.clear()
    
    try:
        users_count = await TGUser.get_users_count(call.bot.db)
        stats_text = (
            f"📊 <b>Статистика бота</b>\n\n"
            f"👥 Всего пользователей: <b>{users_count}</b>\n"
            f"🤖 Бот работает исправно\n"
            f"📦 Функции: накладные, регистрация"
        )
        
        await call.message.edit_text(stats_text, reply_markup=await admin_menu_kb_inline())
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        await call.message.edit_text(
            "❌ Ошибка при получении статистики",
            reply_markup=await admin_menu_kb_inline()
        )


async def admin_download_invoice(call: types.CallbackQuery, state: FSMContext):
    """Скачать накладную в Excel формате"""
    sales_id = int(call.data.split('_')[-1])
    
    logger.info(f"Admin {call.from_user.id} downloading invoice: {sales_id}")
    
    # Показываем загрузку
    await call.message.edit_text("📊 Генерируем Excel файл...")
    
    try:
        # Получаем детали накладной
        details = await TGUser.get_sales_document_details(call.bot.db, sales_id)
        
        if not details:
            await call.message.edit_text(
                "❌ Накладная не найдена",
                reply_markup=await admin_invoice_details_kb_inline(sales_id)
            )
            return
        
        # Преобразуем данные для функции генерации Excel
        # Формат для generate_invoice_excel: (company, code, name, date, operation, quantity, price, amount, status)
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
            reply_markup=await admin_invoice_details_kb_inline(sales_id)
        )
        
    except Exception as e:
        logger.error(f"Error generating invoice Excel: {e}")
        await call.message.edit_text(
            "❌ Ошибка при генерации накладной",
            reply_markup=await admin_invoice_details_kb_inline(sales_id)
        )


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
        admin_stats,
        F.data == "btn_admin_stats",
        AdminFilter()
    )
    router.callback_query.register(
        admin_download_invoice,
        F.data.startswith("btn_admin_download_"),
        AdminFilter()
    )

    return router
