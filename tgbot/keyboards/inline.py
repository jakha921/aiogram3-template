import uuid
from datetime import datetime

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


# back to role
async def back_to_role_kb_inline():
    """Back to role inline keyboard"""
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="⬅️Ortga", callback_data="btn_back_role"))
    return keyboard.as_markup()


async def generate_kb_inline(buttons: list[dict], state):
    """
    Генерирует inline-клавиатуру и сохраняет в состоянии mapping:
    {doc_id: file_url}.
    Каждый элемент buttons должен быть dict с ключами:
      - "text": текст кнопки,
      - "file": URL файла.
    """
    # print('-' * 10)
    # print('buttons', buttons)
    keyboard = InlineKeyboardBuilder()
    mapping = {}
    for btn in buttons:
        # Генерируем короткий уникальный идентификатор
        doc_id = f"ref_{uuid.uuid4().hex[:8]}"
        # Сохраняем связь doc_id -> URL файла
        mapping[doc_id] = f"{btn['file']}|{btn['text'].split(' | ')[0]}"
        keyboard.add(InlineKeyboardButton(text=btn["text"], callback_data=doc_id))
    keyboard.add(InlineKeyboardButton(text="⬅️Ortga", callback_data="btn_docs"))

    # Сохраняем mapping в состоянии (RedisStorage2 уже настроен)
    await state.update_data(doc_mapping=mapping)
    return keyboard.adjust(1).as_markup()


# 12 month names for inline keyboard
async def month_kb_inline():
    """12 month names for inline keyboard"""
    keyboard = InlineKeyboardBuilder()
    months = {
        "01": "Янв",
        "02": "Фев",
        "03": "Мар",
        "04": "Апр",
        "05": "Май",
        "06": "Июн",
        "07": "Июл",
        "08": "Авг",
        "09": "Сен",
        "10": "Окт",
        "11": "Ноя",
        "12": "Дек",
    }
    for month, short in months.items():
        keyboard.add(InlineKeyboardButton(text=short, callback_data=f"btn_month_{month}_{short}"))
    keyboard.add(InlineKeyboardButton(text="⬅️Назад", callback_data="btn_main_menu"))

    return keyboard.adjust(3).as_markup()


async def user_menu_kb_inline():
    """
    User menu inline keyboard
    Накладные, Акт сверки, Контакт
    """
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="📦 Накладные", callback_data="btn_user_invoices")),
    keyboard.add(InlineKeyboardButton(text="📄 Акт сверки", callback_data="btn_user_reconciliation")),
    keyboard.add(InlineKeyboardButton(text="📞 Контакт", callback_data="btn_contact"))

    return keyboard.adjust(2).as_markup()


# Admin keyboards
async def admin_menu_kb_inline():
    """Admin main menu inline keyboard"""
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="📦 Накладные", callback_data="btn_admin_invoices"))
    keyboard.add(InlineKeyboardButton(text="📄 Акт сверки", callback_data="btn_admin_reconciliation_menu"))
    keyboard.add(InlineKeyboardButton(text="📊 Статистика", callback_data="btn_admin_stats"))
    return keyboard.adjust(1).as_markup()


async def admin_years_kb_inline():
    """Years selection for admin invoices filter"""
    keyboard = InlineKeyboardBuilder()
    current_year = datetime.now().year
    
    # Добавляем последние 5 лет
    for year in range(current_year, current_year - 5, -1):
        keyboard.add(InlineKeyboardButton(text=str(year), callback_data=f"btn_admin_year_{year}"))
    
    keyboard.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="btn_admin_menu"))
    return keyboard.adjust(2).as_markup()


async def admin_months_kb_inline():
    """Months selection for admin invoices filter"""
    keyboard = InlineKeyboardBuilder()
    months = {
        "01": "Январь",
        "02": "Февраль", 
        "03": "Март",
        "04": "Апрель",
        "05": "Май",
        "06": "Июнь",
        "07": "Июль",
        "08": "Август",
        "09": "Сентябрь",
        "10": "Октябрь",
        "11": "Ноябрь",
        "12": "Декабрь",
    }
    
    for month, name in months.items():
        keyboard.add(InlineKeyboardButton(text=name, callback_data=f"btn_admin_month_{month}"))
    
    keyboard.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="btn_admin_invoices"))
    keyboard.add(InlineKeyboardButton(text="🏠 Главное меню", callback_data="btn_admin_menu"))
    return keyboard.adjust(3).as_markup()


async def admin_invoices_list_kb_inline(invoices_data: list):
    """Generate keyboard for invoices list with pagination"""
    keyboard = InlineKeyboardBuilder()
    
    # Ограничиваем до 10 накладных на страницу
    max_items = min(len(invoices_data), 10)
    
    for i, invoice in enumerate(invoices_data[:max_items]):
        # Форматируем текст кнопки
        invoice_text = f"📋 {invoice['Покупатель'][:20]}{'...' if len(invoice['Покупатель']) > 20 else ''} | {invoice['Сумма продажи']:,.0f} сум"
        keyboard.add(InlineKeyboardButton(
            text=invoice_text, 
            callback_data=f"btn_admin_invoice_details_{invoice['Код']}"
        ))
    
    keyboard.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="btn_admin_invoices"))
    return keyboard.adjust(1).as_markup()


async def admin_invoice_details_kb_inline(sales_id: int):
    """Back button for invoice details with download option"""
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="📄 Скачать накладную", callback_data=f"btn_admin_download_{sales_id}"))
    keyboard.add(InlineKeyboardButton(text="⬅️ К списку накладных", callback_data="btn_admin_back_to_list"))
    
    return keyboard.adjust(1).as_markup()


async def admin_reconciliation_kb_inline(sales_id: int):
    keyboard = InlineKeyboardBuilder()
    keyboard.add(InlineKeyboardButton(text="📄 Скачать акт сверки", callback_data=f"btn_admin_reconciliation_{sales_id}"))
    keyboard.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="btn_admin_menu"))
    return keyboard.adjust(1).as_markup()


def years_keyboard(years):
    kb = InlineKeyboardMarkup(row_width=3)
    for year in years:
        kb.insert(InlineKeyboardButton(str(year), callback_data=f"act_year_{year}"))
    return kb

def months_keyboard(months, year):
    kb = InlineKeyboardMarkup(row_width=4)
    for month in months:
        kb.insert(InlineKeyboardButton(str(month), callback_data=f"act_month_{year}_{month}"))
    return kb

def customers_keyboard(customers, year, month):
    kb = InlineKeyboardMarkup(row_width=1)
    for c in customers:
        kb.insert(InlineKeyboardButton(f"{c['name']} ({c['phone']})", callback_data=f"act_customer_{year}_{month}_{c['phone']}"))
    return kb


async def user_reconciliation_years_kb_inline():
    """Years selection for user reconciliation"""
    keyboard = InlineKeyboardBuilder()
    current_year = datetime.now().year
    
    # Добавляем последние 5 лет
    for year in range(current_year, current_year - 5, -1):
        keyboard.add(InlineKeyboardButton(text=str(year), callback_data=f"btn_user_recon_year_{year}"))
    
    keyboard.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="btn_main_menu"))
    return keyboard.adjust(2).as_markup()


async def user_reconciliation_months_kb_inline():
    """Months selection for user reconciliation"""
    keyboard = InlineKeyboardBuilder()
    months = {
        "01": "Январь", "02": "Февраль", "03": "Март", "04": "Апрель",
        "05": "Май", "06": "Июнь", "07": "Июль", "08": "Август",
        "09": "Сентябрь", "10": "Октябрь", "11": "Ноябрь", "12": "Декабрь"
    }
    
    for month, name in months.items():
        keyboard.add(InlineKeyboardButton(text=name, callback_data=f"btn_user_recon_month_{month}"))
    
    keyboard.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="btn_user_reconciliation"))
    keyboard.add(InlineKeyboardButton(text="🏠 Главное меню", callback_data="btn_main_menu"))
    return keyboard.adjust(3).as_markup()


async def user_invoices_years_kb_inline():
    """Years selection for user invoices"""
    keyboard = InlineKeyboardBuilder()
    current_year = datetime.now().year
    
    # Добавляем последние 5 лет
    for year in range(current_year, current_year - 5, -1):
        keyboard.add(InlineKeyboardButton(text=str(year), callback_data=f"btn_user_invoice_year_{year}"))
    
    keyboard.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="btn_main_menu"))
    return keyboard.adjust(2).as_markup()


async def user_invoices_months_kb_inline():
    """Months selection for user invoices"""
    keyboard = InlineKeyboardBuilder()
    months = {
        "01": "Январь", "02": "Февраль", "03": "Март", "04": "Апрель",
        "05": "Май", "06": "Июнь", "07": "Июль", "08": "Август",
        "09": "Сентябрь", "10": "Октябрь", "11": "Ноябрь", "12": "Декабрь"
    }
    
    for month, name in months.items():
        keyboard.add(InlineKeyboardButton(text=name, callback_data=f"btn_user_invoice_month_{month}"))
    
    keyboard.add(InlineKeyboardButton(text="⬅️ Назад", callback_data="btn_user_invoices"))
    keyboard.add(InlineKeyboardButton(text="🏠 Главное меню", callback_data="btn_main_menu"))
    return keyboard.adjust(3).as_markup()
