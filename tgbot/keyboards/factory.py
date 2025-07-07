from typing import List, Dict, Any
from datetime import datetime
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


class KeyboardFactory:
    """Фабрика для создания клавиатур"""
    
    @staticmethod
    def admin_menu() -> InlineKeyboardMarkup:
        """Главное админское меню"""
        kb = InlineKeyboardBuilder()
        kb.button(text="📦 Накладные", callback_data="btn_admin_invoices")
        kb.button(text="📄 Акт сверки", callback_data="btn_admin_reconciliation_menu")
        kb.button(text="📊 Статистика", callback_data="btn_admin_stats")
        return kb.adjust(1).as_markup()
    
    @staticmethod
    def years_selection(current_year: int = None, prefix: str = "btn_admin_year_", back_callback: str = "btn_admin_menu") -> InlineKeyboardMarkup:
        """Выбор года"""
        kb = InlineKeyboardBuilder()
        if current_year is None:
            current_year = datetime.now().year
        
        # Добавляем последние 5 лет
        for year in range(current_year, current_year - 5, -1):
            kb.button(text=str(year), callback_data=f"{prefix}{year}")
        
        kb.button(text="⬅️ Назад", callback_data=back_callback)
        return kb.adjust(2).as_markup()
    
    @staticmethod
    def months_selection(prefix: str = "btn_admin_month_", back_callback: str = "btn_admin_invoices") -> InlineKeyboardMarkup:
        """Выбор месяца"""
        kb = InlineKeyboardBuilder()
        months = {
            "01": "Январь", "02": "Февраль", "03": "Март", "04": "Апрель",
            "05": "Май", "06": "Июнь", "07": "Июль", "08": "Август",
            "09": "Сентябрь", "10": "Октябрь", "11": "Ноябрь", "12": "Декабрь"
        }
        
        for month, name in months.items():
            kb.button(text=name, callback_data=f"{prefix}{month}")
        
        kb.button(text="⬅️ Назад", callback_data=back_callback)
        kb.button(text="🏠 Главное меню", callback_data="btn_admin_menu")
        return kb.adjust(3).as_markup()
    
    @staticmethod
    def invoices_list(invoices_data: List[Dict[str, Any]], page: int = 0, per_page: int = 10) -> InlineKeyboardMarkup:
        """Список накладных с пагинацией"""
        kb = InlineKeyboardBuilder()
        start_idx = page * per_page
        end_idx = start_idx + per_page
        page_invoices = invoices_data[start_idx:end_idx]
        for invoice in page_invoices:
            customer_name = invoice['Покупатель'][:20]
            if len(invoice['Покупатель']) > 20:
                customer_name += "..."
            invoice_text = f"📋 {customer_name} | {invoice['Сумма продажи']:,.0f} сум"
            kb.row(
                InlineKeyboardButton(
                    text=invoice_text,
                    callback_data=f"btn_admin_invoice_details_{invoice['Код']}"
                )
            )
        total_pages = (len(invoices_data) + per_page - 1) // per_page
        pagination_row = []
        if total_pages > 1:
            if page > 0:
                pagination_row.append(("⬅️", f"btn_admin_page_{page-1}"))
            pagination_row.append((f"{page+1}/{total_pages}", "btn_admin_page_info"))
            if page < total_pages - 1:
                pagination_row.append(("➡️", f"btn_admin_page_{page+1}"))
            kb.row(*[InlineKeyboardButton(text=text, callback_data=cb) for text, cb in pagination_row])
        kb.row(
            InlineKeyboardButton(text="⬅️ Назад", callback_data="btn_admin_invoices"),
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="btn_admin_menu")
        )
        return kb.as_markup()

    @staticmethod
    def invoice_details(sales_id: int) -> InlineKeyboardMarkup:
        """Детали накладной с кнопкой скачивания"""
        kb = InlineKeyboardBuilder()
        kb.button(text="📄 Скачать накладную", callback_data=f"btn_admin_download_{sales_id}")
        kb.button(text="⬅️ К списку накладных", callback_data="btn_admin_back_to_list")
        return kb.adjust(1).as_markup()
    
    @staticmethod
    def reconciliation_menu(phone: str) -> InlineKeyboardMarkup:
        """Меню акта сверки"""
        kb = InlineKeyboardBuilder()
        kb.button(text="📄 Скачать акт сверки", callback_data=f"btn_admin_reconciliation_{phone}")
        kb.button(text="⬅️ Назад", callback_data="btn_admin_menu")
        return kb.adjust(1).as_markup()
    
    @staticmethod
    def reconciliation_documents(act_data: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
        """Список документов для акта сверки"""
        kb = InlineKeyboardBuilder()
        
        for i, row in enumerate(act_data):
            text = f"{row['Дата'].strftime('%d.%m.%Y')} | {row['Документ']} | {row['Сумма']:,.0f} сум"
            kb.button(text=text, callback_data=f"btn_admin_recon_doc_{i}")
        
        return kb.adjust(1).as_markup()
    
    @staticmethod
    def act_years(years: List[int]) -> InlineKeyboardMarkup:
        """Выбор года для акта сверки"""
        kb = InlineKeyboardBuilder()
        for year in years:
            kb.button(text=str(year), callback_data=f"act_year_{year}")
        return kb.adjust(3).as_markup()
    
    @staticmethod
    def act_months(months: List[int], year: int) -> InlineKeyboardMarkup:
        """Выбор месяца для акта сверки"""
        kb = InlineKeyboardBuilder()
        for month in months:
            kb.button(text=str(month), callback_data=f"act_month_{year}_{month}")
        return kb.adjust(4).as_markup()
    
    @staticmethod
    def act_customers(customers: List[Dict[str, Any]], year: int, month: int) -> InlineKeyboardMarkup:
        """Выбор покупателя для акта сверки (с суммой)"""
        kb = InlineKeyboardBuilder()
        for customer in customers:
            customer_name = customer['name'][:20]
            if len(customer['name']) > 20:
                customer_name += "..."
            if 'total_sum' in customer:
                text = f"📋 {customer_name} | {customer['total_sum']:,.0f} сум"
            else:
                text = f"📋 {customer_name} {customer['phone']}" if customer['phone'] else f'📋 {customer_name}'
            kb.row(
                InlineKeyboardButton(
                    text=text,
                    callback_data=f"act_customer_{year}_{month}_{customer['phone']}"
                )
            )
        return kb.as_markup()
    
    @staticmethod
    def act_download(year: int, month: int, phone: str) -> InlineKeyboardMarkup:
        """Кнопка скачивания акта сверки"""
        kb = InlineKeyboardBuilder()
        kb.row(
            InlineKeyboardButton(text="📄 Скачать акт сверки", callback_data=f"act_download_{year}_{month}_{phone}"),
        )
        kb.row(
            InlineKeyboardButton(text="⬅️ К списку актов сверки", callback_data=f"recon_customers_page_{year}_{month}_0"),
            # InlineKeyboardButton(text="⬅️ Назад", callback_data="btn_admin_reconciliation_menu"),
            # InlineKeyboardButton(text="🏠 Главное меню", callback_data="btn_admin_menu")
        )
        return kb.as_markup()
    
    @staticmethod
    def reconciliation_excel_download_kb(year: int, month: int, phone: str) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        kb.row(
            InlineKeyboardButton(
                text="📄 Скачать акт сверки",
                callback_data=f"recon_download_excel_{year}_{month}_{phone}"
            ),
            InlineKeyboardButton(
                text="⬅️ К списку актов сверки",
                callback_data=f"recon_customers_page_{year}_{month}_0"
            )
        )
        kb.row(
            InlineKeyboardButton(text="⬅️ К списку актов сверки", callback_data=f"recon_customers_page_{year}_{month}_0"),
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="btn_admin_menu")
        )
        return kb.adjust(1).as_markup()
    
    @staticmethod
    def reconciliation_customers_list(customers: List[Dict[str, Any]], year: int, month: int, page: int = 0, per_page: int = 10) -> InlineKeyboardMarkup:
        kb = InlineKeyboardBuilder()
        start_idx = page * per_page
        end_idx = start_idx + per_page
        page_customers = customers[start_idx:end_idx]
        for customer in page_customers:
            text = f"{customer['name']} ({customer['phone']})"
            kb.row(
                InlineKeyboardButton(
                    text=text,
                    callback_data=f"act_customer_{year}_{month}_{customer['phone']}"
                )
            )
        total_pages = (len(customers) + per_page - 1) // per_page
        pagination_row = []
        if total_pages > 1:
            if page > 0:
                pagination_row.append(("⬅️", f"recon_customers_page_{year}_{month}_{page-1}"))
            pagination_row.append((f"{page+1}/{total_pages}", "recon_customers_page_info"))
            if page < total_pages - 1:
                pagination_row.append(("➡️", f"recon_customers_page_{year}_{month}_{page+1}"))
            kb.row(*[InlineKeyboardButton(text=text, callback_data=cb) for text, cb in pagination_row])
        kb.row(
            InlineKeyboardButton(text="⬅️ Назад", callback_data="btn_admin_reconciliation_menu"),
            InlineKeyboardButton(text="🏠 Главное меню", callback_data="btn_admin_menu")
        )
        return kb.as_markup() 