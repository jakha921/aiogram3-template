from typing import List, Dict, Any, Optional
from datetime import datetime
from loguru import logger
from tgbot.services.base_service import BaseService
from tgbot.services.cache_service import cache_service


class AdminService(BaseService):
    """Сервис для админских операций"""
    
    async def get_users_count(self) -> int:
        """Получить количество пользователей"""
        from tgbot.models.models import TGUser
        return await self.safe_execute(
            "get_users_count",
            TGUser.get_users_count,
            self.db
        )
    
    async def get_invoices_by_period(self, year: int, month: int) -> List[Dict[str, Any]]:
        """Получить накладные за период с кэшированием"""
        from tgbot.models.models import TGUser
        cache_key = f"admin_invoices_{year}_{month}"
        return await self.get_cached_data(
            cache_key,
            lambda: TGUser.get_sales_invoices_by_period(self.db, year, month),
            ttl_seconds=600
        )
    
    async def get_invoice_details(self, sales_id: int) -> Optional[List[Dict[str, Any]]]:
        """Получить детали накладной с кэшированием"""
        from tgbot.models.models import TGUser
        cache_key = f"admin_invoice_details_{sales_id}"
        return await self.get_cached_data(
            cache_key,
            lambda: TGUser.get_sales_document_details(self.db, sales_id),
            ttl_seconds=300
        )
    
    async def get_reconciliation_data(self, phone: str, year: int, month: int) -> List[Dict[str, Any]]:
        """Получить данные для акта сверки с кэшированием"""
        from tgbot.models.models import TGUser
        cache_key = f"admin_reconciliation_{phone}_{year}_{month}"
        return await self.get_cached_data(
            cache_key,
            lambda: TGUser.get_customer_sales_summary(self.db, phone, year, month),
            ttl_seconds=600
        )
    
    async def get_sales_years(self) -> List[int]:
        """Получить список годов с продажами с кэшированием"""
        from tgbot.models.models import TGUser
        return await self.get_cached_data(
            "admin_sales_years",
            lambda: TGUser.get_sales_years(self.db),
            ttl_seconds=3600
        )
    
    async def get_sales_months(self, year: int) -> List[int]:
        """Получить список месяцев с продажами за год с кэшированием"""
        from tgbot.models.models import TGUser
        cache_key = f"admin_sales_months_{year}"
        return await self.get_cached_data(
            cache_key,
            lambda: TGUser.get_sales_months(self.db, year),
            ttl_seconds=3600
        )
    
    async def get_customers_by_period(self, year: int, month: int) -> List[Dict[str, Any]]:
        """Получить список покупателей за период с кэшированием"""
        from tgbot.models.models import TGUser
        cache_key = f"admin_customers_{year}_{month}"
        return await self.get_cached_data(
            cache_key,
            lambda: TGUser.get_customers_by_period(self.db, year, month),
            ttl_seconds=1800
        )
    
    async def get_all_customers_with_sales(self) -> List[Dict[str, Any]]:
        """Получить полный список покупателей, у которых были продажи"""
        from tgbot.models.models import TGUser
        from sqlalchemy import text
        async def _get_all_customers():
            # Получаем всех покупателей с продажами (без фильтра по периоду)
            async with self.db() as session:
                stmt = text("""
                    SELECT DISTINCT 
                        c.cstm_id as id,
                        c.cstm_name as name,
                        c.cstm_phone as phone
                    FROM doc_sales AS s 
                    JOIN dir_customers AS c ON s.sls_customer = c.cstm_id
                    WHERE s.sls_performed = 1 AND s.sls_deleted = 0
                    ORDER BY c.cstm_name
                """)
                result = await session.execute(stmt)
                return [row._asdict() for row in result.fetchall()]
        
        return await self.get_cached_data("all_customers", _get_all_customers, ttl_seconds=3600)
    
    def format_invoice_summary(self, invoices: List[Dict[str, Any]], year: int, month: int) -> str:
        """Форматировать сводку накладных"""
        if not invoices:
            return f"❌ За {month}/{year} накладные не найдены"
        
        total_sum = sum(invoice['Сумма продажи'] for invoice in invoices)
        return (
            f"📦 <b>Накладные за {month}/{year}</b>\n\n"
            f"📊 Найдено: {len(invoices)} накладных\n"
            f"💰 Общая сумма: {self.format_currency(total_sum)}\n\n"
            f"Выберите накладную для детального просмотра:"
        )
    
    def format_invoice_details(self, details: List[Dict[str, Any]], sales_id: int) -> str:
        """Форматировать детали накладной"""
        if not details:
            return "❌ Детали накладной не найдены"
        
        first_item = details[0]
        header = (
            f"📋 <b>Накладная #{sales_id}</b>\n"
            f"🏪 Магазин: {first_item['Магазин/Склад']}\n"
            f"📅 Дата: {self.format_date(first_item['Дата/Время'])}\n\n"
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
                f"  Цена: {self.format_currency(item['Цена'])}\n"
                f"  Сумма: {self.format_currency(item_total)}"
            )
        
        # Ограничиваем количество товаров для отображения
        if len(items_text) > 10:
            displayed_items = items_text[:10]
            displayed_items.append(f"\n... и еще {len(items_text) - 10} товаров")
        else:
            displayed_items = items_text
        
        footer = f"\n\n💰 <b>Итого: {self.format_currency(total_sum)}</b>"
        
        full_text = header + "\n\n".join(displayed_items) + footer
        
        # Проверяем длину сообщения (ограничение Telegram)
        if len(full_text) > 4000:
            # Сокращаем количество товаров
            short_items = items_text[:5]
            short_items.append(f"\n... и еще {len(items_text) - 5} товаров")
            full_text = header + "\n\n".join(short_items) + footer
        
        return full_text
    
    def format_reconciliation_text(self, summary: List[Dict[str, Any]], customer_name: str, year: int, month: int, customer_phone: str = None) -> str:
        """Форматировать текст акта сверки для UX как у накладных"""
        max_rows = 10
        docs_shown = summary[:max_rows]
        total_debt = sum(float(row.get('Долг', 0) or 0) for row in summary)
        total_sum = sum(float(row.get('Сумма', 0) or 0) for row in summary)
        period_str = f"{month:02d}/{year}"
        phone_str = f" ({customer_phone})" if customer_phone else ""
        header = (
            f"📄 <b>Акт сверки за {period_str}</b>\n"
            f"👤 Покупатель: <b>{customer_name}{phone_str}</b>\n\n"
            f"📊 Найдено: {len(summary)} документов\n"
            f"💵 Общая сумма за период: <b>{self.format_currency(total_sum)}</b>\n"
            f"💰 Итоговый долг: <b>{self.format_currency(total_debt)}</b>\n"
        )
        if len(summary) > max_rows:
            header += f"\nПоказаны первые {max_rows} документов..."
        header += "\n(подробности — в Excel)"
        return header
    
    async def clear_cache(self) -> None:
        """Очистить кэш"""
        await cache_service.clear()
        logger.info("Cache cleared")
    
    async def invalidate_invoice_cache(self, year: int = None, month: int = None) -> None:
        """Инвалидировать кэш накладных"""
        if year and month:
            key = cache_service._generate_key("invoices", year=year, month=month)
            await cache_service.delete(key)
        else:
            # Удаляем все ключи, связанные с накладными
            keys_to_delete = []
            for key in cache_service._cache.keys():
                if key.startswith("invoices_"):
                    keys_to_delete.append(key)
            
            for key in keys_to_delete:
                await cache_service.delete(key)
        
        logger.info(f"Invoice cache invalidated for year={year}, month={month}")

    def filter_reconciliation_data_by_period(self, summary: list, year: int, month: int) -> list:
        """Фильтрует данные акта сверки по году и месяцу"""
        return [row for row in summary if hasattr(row['Дата'], 'year') and row['Дата'].year == year and row['Дата'].month == month]

    def get_reconciliation_excel_params(self, customer_name: str, year: int, month: int, filtered_summary: list) -> dict:
        """Готовит параметры для Excel-акта сверки"""
        company1 = "AVTOLIDER"
        company2 = customer_name
        period_start = f"01.{month:02d}.{year}"
        period_end = f"31.{month:02d}.{year}"
        saldo_start = 0.0
        saldo_end = filtered_summary[-1]['Долг'] if filtered_summary else 0.0
        
        return {
            "company1": company1,
            "company2": company2,
            "period_start": period_start,
            "period_end": period_end,
            "saldo_start": saldo_start,
            "saldo_end": saldo_end
        } 