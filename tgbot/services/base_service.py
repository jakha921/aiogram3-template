from typing import Any, Dict, List, Optional
from loguru import logger
from tgbot.services.cache_service import cache_service


class BaseService:
    """Базовый сервис с общей функциональностью"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    async def safe_execute(self, operation_name: str, operation_func, *args, **kwargs) -> Optional[Any]:
        """Безопасное выполнение операций с обработкой ошибок"""
        try:
            return await operation_func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {operation_name}: {e}")
            raise
    
    def format_currency(self, amount: float) -> str:
        """Форматирование валюты"""
        return f"{amount:,.0f} сум"
    
    def format_date(self, date_obj) -> str:
        """Форматирование даты"""
        if hasattr(date_obj, 'strftime'):
            return date_obj.strftime('%d.%m.%Y')
        return str(date_obj)
    
    def truncate_text(self, text: str, max_length: int = 50) -> str:
        """Обрезка текста с добавлением многоточия"""
        if len(text) <= max_length:
            return text
        return text[:max_length-3] + "..."
    
    async def get_cached_data(self, cache_key: str, getter_func, ttl_seconds: int = 300):
        """Получение данных с кэшированием"""
        return await cache_service.get_or_set(cache_key, getter_func, ttl_seconds) 