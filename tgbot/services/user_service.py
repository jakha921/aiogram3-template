from typing import List, Dict, Any, Optional
from loguru import logger
from tgbot.services.base_service import BaseService
from tgbot.models.models import TGUser
from tgbot.services.cache_service import cache_service


class UserService(BaseService):
    """Сервис для пользовательских операций"""
    
    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[TGUser]:
        """Получить пользователя по Telegram ID"""
        return await self.safe_execute(
            "get_user_by_telegram_id",
            TGUser.get_user,
            self.db,
            telegram_id
        )
    
    async def update_user_phone(self, telegram_id: int, phone: str) -> Optional[TGUser]:
        """Обновить номер телефона пользователя"""
        return await self.safe_execute(
            "update_user_phone",
            TGUser.update_user,
            self.db,
            telegram_id,
            phone=phone
        )
    
    async def get_user_invoice(self, phone: str, month: str) -> List[Dict[str, Any]]:
        """Получить накладную пользователя"""
        cache_key = f"user_invoice_{phone}_{month}"
        return await self.get_cached_data(
            cache_key,
            lambda: TGUser.get_user_invoice(self.db, phone, month),
            ttl_seconds=600
        )
    
    async def get_user_reconciliation(self, phone: str, year: int, month: int) -> List[Dict[str, Any]]:
        """Получить данные акта сверки пользователя"""
        cache_key = f"user_reconciliation_{phone}_{year}_{month}"
        return await self.get_cached_data(
            cache_key,
            lambda: TGUser.get_customer_sales_summary(self.db, phone, year, month),
            ttl_seconds=600
        )
    
    async def get_customer_name(self, phone: str) -> str:
        """Получить название покупателя по номеру телефона"""
        cache_key = f"customer_name_{phone}"
        return await self.get_cached_data(
            cache_key,
            lambda: TGUser.get_customer_name_by_phone(self.db, phone),
            ttl_seconds=3600
        )
    
    def format_reconciliation_summary(self, summary: List[Dict[str, Any]], phone: str, year: int, month: int) -> str:
        """Форматировать сводку акта сверки"""
        if not summary:
            return f"❌ За {month}/{year} данные для акта сверки не найдены"
        
        total_debt = sum(float(row.get('Долг', 0) or 0) for row in summary)
        total_sum = sum(float(row.get('Сумма', 0) or 0) for row in summary)
        
        return (
            f"📄 <b>Акт сверки за {month}/{year}</b>\n"
            f"📱 Телефон: <b>{phone}</b>\n\n"
            f"📊 Найдено: {len(summary)} документов\n"
            f"💵 Общая сумма за период: <b>{self.format_currency(total_sum)}</b>\n"
            f"💰 Итоговый долг: <b>{self.format_currency(total_debt)}</b>\n\n"
            "📄 Генерируем Excel файл..."
        )
    
    def get_reconciliation_excel_params(self, customer_name: str, year: int, month: int, total_debt: float) -> Dict[str, Any]:
        """Получить параметры для Excel файла акта сверки"""
        return {
            "company1": "AVTOLIDER",
            "company2": customer_name,
            "period_start": f"01.{month}.{year}",
            "period_end": f"31.{month}.{year}",
            "saldo_start": 0.0,
            "saldo_end": total_debt
        } 