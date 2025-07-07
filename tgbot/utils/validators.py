"""Утилиты для валидации данных"""

import re
from typing import Optional


def validate_phone_number(phone: str) -> Optional[str]:
    """
    Валидация номера телефона
    
    Args:
        phone: Номер телефона для валидации
        
    Returns:
        Отформатированный номер телефона или None если невалидный
    """
    if not phone:
        return None
    
    # Убираем все пробелы и дефисы
    phone = re.sub(r'[\s\-]', '', phone)
    
    # Проверяем формат +998XXXXXXXXX
    if re.match(r'^\+998\d{9}$', phone):
        return phone[1:]  # Убираем +
    
    # Проверяем формат 998XXXXXXXXX
    if re.match(r'^998\d{9}$', phone):
        return phone
    
    # Проверяем формат 9XXXXXXXXX (добавляем 998)
    if re.match(r'^9\d{8}$', phone):
        return f"998{phone}"
    
    return None


def validate_year(year: str) -> Optional[int]:
    """
    Валидация года
    
    Args:
        year: Год для валидации
        
    Returns:
        Год как int или None если невалидный
    """
    try:
        year_int = int(year)
        if 2000 <= year_int <= 2100:
            return year_int
    except (ValueError, TypeError):
        pass
    return None


def validate_month(month: str) -> Optional[str]:
    """
    Валидация месяца
    
    Args:
        month: Месяц для валидации
        
    Returns:
        Месяц в формате MM или None если невалидный
    """
    try:
        month_int = int(month)
        if 1 <= month_int <= 12:
            return f"{month_int:02d}"
    except (ValueError, TypeError):
        pass
    return None 