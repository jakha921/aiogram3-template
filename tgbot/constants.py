"""Константы для Telegram бота"""

# Названия компаний
COMPANY_NAME = "AVTOLIDER"

# Форматы дат
DATE_FORMAT = "%d.%m.%Y"
DATETIME_FORMAT = "%d.%m.%Y %H:%M"

# Лимиты
MAX_INVOICE_ITEMS_DISPLAY = 10
MAX_INVOICE_ITEMS_SHORT = 5
MAX_MESSAGE_LENGTH = 4000
MAX_CUSTOMER_NAME_LENGTH = 50

# TTL для кэширования (в секундах)
CACHE_TTL = {
    "INVOICES": 600,  # 10 минут
    "INVOICE_DETAILS": 300,  # 5 минут
    "RECONCILIATION": 600,  # 10 минут
    "SALES_YEARS": 3600,  # 1 час
    "SALES_MONTHS": 3600,  # 1 час
    "CUSTOMERS": 1800,  # 30 минут
    "CUSTOMER_NAME": 3600,  # 1 час
    "USER_INVOICE": 600,  # 10 минут
    "USER_RECONCILIATION": 600,  # 10 минут
}

# Названия месяцев
MONTH_NAMES = {
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

# Короткие названия месяцев
MONTH_NAMES_SHORT = {
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

# Сообщения об ошибках
ERROR_MESSAGES = {
    "PHONE_NOT_FOUND": "❌ Номер телефона не найден. Обратитесь к администратору.",
    "INVOICE_NOT_FOUND": "❗️ <b>За указанный месяц счёт не найден.</b>",
    "RECONCILIATION_NOT_FOUND": "❌ За {month}/{year} данные для акта сверки не найдены",
    "GENERAL_ERROR": "❌ Произошла ошибка. Попробуйте позже.",
    "INVOICE_GENERATION_ERROR": "❌ Ошибка при генерации накладной",
    "RECONCILIATION_GENERATION_ERROR": "❌ Ошибка при генерации акта сверки",
}

# Сообщения успеха
SUCCESS_MESSAGES = {
    "PHONE_SAVED": "Ваш номер телефона сохранен: {phone}",
    "WELCOME": "Добро пожаловать, {name}!",
    "INVOICE_READY": "📄 Ваша накладная за {month} {year} готова!",
    "RECONCILIATION_READY": "📄 Ваш акт сверки за {period_start} - {period_end} готов!",
}

# Эмодзи
EMOJI = {
    "INVOICE": "📦",
    "RECONCILIATION": "📄",
    "CONTACT": "📞",
    "MAIN_MENU": "🏠",
    "BACK": "⬅️",
    "LOADING": "🔄",
    "SUCCESS": "✅",
    "ERROR": "❌",
    "WARNING": "❗️",
    "INFO": "ℹ️",
    "MONEY": "💰",
    "CALENDAR": "📅",
    "DOCUMENT": "📋",
    "STORE": "🏪",
    "USER": "👤",
    "PHONE": "📱",
    "STATS": "📊",
    "SUM": "💵",
} 