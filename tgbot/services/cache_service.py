import asyncio
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
from loguru import logger


class CacheService:
    """Сервис кэширования для оптимизации производительности"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()
    
    async def get(self, key: str) -> Optional[Any]:
        """Получить значение из кэша"""
        async with self._lock:
            if key in self._cache:
                cache_item = self._cache[key]
                if datetime.now() < cache_item['expires_at']:
                    return cache_item['value']
                else:
                    # Удаляем просроченный кэш
                    del self._cache[key]
            return None
    
    async def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """Установить значение в кэш с TTL"""
        async with self._lock:
            self._cache[key] = {
                'value': value,
                'expires_at': datetime.now() + timedelta(seconds=ttl_seconds)
            }
    
    async def delete(self, key: str) -> None:
        """Удалить значение из кэша"""
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
    
    async def clear(self) -> None:
        """Очистить весь кэш"""
        async with self._lock:
            self._cache.clear()
    
    async def get_or_set(self, key: str, getter_func, ttl_seconds: int = 300) -> Any:
        """Получить из кэша или установить новое значение"""
        cached_value = await self.get(key)
        if cached_value is not None:
            return cached_value
        
        # Получаем новое значение
        try:
            new_value = await getter_func()
            await self.set(key, new_value, ttl_seconds)
            return new_value
        except Exception as e:
            logger.error(f"Error in get_or_set for key {key}: {e}")
            raise
    
    def _generate_key(self, prefix: str, **kwargs) -> str:
        """Генерировать ключ кэша"""
        key_parts = [prefix]
        for k, v in sorted(kwargs.items()):
            key_parts.append(f"{k}:{v}")
        return "_".join(key_parts)
    
    async def cache_invoices_by_period(self, year: int, month: int, getter_func) -> List[Dict[str, Any]]:
        """Кэшировать накладные за период"""
        key = self._generate_key("invoices", year=year, month=month)
        return await self.get_or_set(key, getter_func, ttl_seconds=600)  # 10 минут
    
    async def cache_invoice_details(self, sales_id: int, getter_func) -> Optional[List[Dict[str, Any]]]:
        """Кэшировать детали накладной"""
        key = self._generate_key("invoice_details", sales_id=sales_id)
        return await self.get_or_set(key, getter_func, ttl_seconds=300)  # 5 минут
    
    async def cache_reconciliation_data(self, phone: str, year: int, month: int, getter_func) -> List[Dict[str, Any]]:
        """Кэшировать данные акта сверки"""
        key = self._generate_key("reconciliation", phone=phone, year=year, month=month)
        return await self.get_or_set(key, getter_func, ttl_seconds=600)  # 10 минут
    
    async def cache_sales_years(self, getter_func) -> List[int]:
        """Кэшировать список годов"""
        key = self._generate_key("sales_years")
        return await self.get_or_set(key, getter_func, ttl_seconds=3600)  # 1 час
    
    async def cache_sales_months(self, year: int, getter_func) -> List[int]:
        """Кэшировать список месяцев за год"""
        key = self._generate_key("sales_months", year=year)
        return await self.get_or_set(key, getter_func, ttl_seconds=3600)  # 1 час
    
    async def cache_customers_by_period(self, year: int, month: int, getter_func) -> List[Dict[str, Any]]:
        """Кэшировать список покупателей за период"""
        key = self._generate_key("customers", year=year, month=month)
        return await self.get_or_set(key, getter_func, ttl_seconds=1800)  # 30 минут


# Глобальный экземпляр кэша
cache_service = CacheService() 