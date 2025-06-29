# Telegram Bot - Post Terminal

Telegram бот для работы с накладными и пользователями.

## Основной функционал

### Для пользователей:
- 📝 Регистрация с номером телефона
- 📦 Просмотр личных накладных по месяцам
- 📞 Контактная информация
- 📄 Экспорт накладных в Excel

### Для администраторов:
- 📊 Статистика пользователей  
- 📦 **Управление накладными с фильтрацией**:
  - 📅 Фильтр по году и месяцу
  - 📋 Просмотр списка всех накладных за период
  - 💰 Отображение общей суммы продаж
  - 🔍 Детальный просмотр конкретной накладной с товарами
  - 🏪 Информация о магазине и покупателе

## Команды

### Пользовательские:
- `/start` - Начать работу с ботом

### Администраторские:
- `/admin` - Открыть админ панель
- `/stats` - Показать статистику пользователей

## Архитектура

### База данных
Используются два основных метода для работы с накладными:

1. **`get_all_sales_invoices_summary()`** - получение сводки всех накладных:
   - Код накладной
   - Дата/время
   - Магазин/склад  
   - Статус документа
   - Покупатель
   - Общая сумма продажи

2. **`get_sales_document_details(sales_id)`** - детальная информация по накладной:
   - Код товара и наименование
   - Количество и цена
   - Сумма по позиции
   - Дата/время и магазин

### Состояния (FSM)
- `GetPhone` - для регистрации пользователей
- `AdminInvoicesFilter` - для админского функционала:
  - `year` - выбор года
  - `month` - выбор месяца  
  - `invoices_list` - просмотр списка накладных
  - `invoice_details` - детальный просмотр

### Клавиатуры
- Пользовательские: регистрация, накладные, контакты
- Админские: меню, выбор года/месяца, список накладных, детали

## Настройка

1. Установить зависимости: `pip install -r requirements.txt`
2. Настроить переменные окружения в `.env`
3. Запустить: `python bot.py`

## Структура проекта

```bash
├───logs # logs folder
└───tgbot
    ├───filters
    ├───handlers
    ├───keyboards
    ├───middlewares
    ├───misc # misc stuff
    ├───models # database models
    ├───services # services
    ├───config.py # config
    └───states.py # states
```


#### Files:

* The `tgbot` package is the root package for the bot, and it contains sub-packages for filters, handlers, and middlewares.

* The `filters` package contains classes that define custom filters for the bot's message handlers.

* The `handlers` package contains classes that define the bot's message handlers, which specify the actions to take in response to incoming messages.

* The `middlewares` package contains classes that define custom middlewares for the bot's dispatcher, which can be used to perform additional processing on incoming messages.

* The `models` package contains database models.

* The `services` package contains services.


Simple template for bots written on [aiogram](https://github.com/aiogram/aiogram).

### Setting up


#### Preparations

* Clone this repo via `https://github.com/jakha921/aiogram3-template.git`

* Create virtual environment: `python -m venv venv`
* Make **venv** your source: `source ./venv/bin/activate` (Linux) or `.\venv\Scripts\activate (Windows)`
* Install requirements: `pip install -r requirements.txt`


### Deployment

* Copy `.env.example` to `.env` and set your variables.

* Run bot: `python bot.py`


### Useful

**Commands:**
* `/start` - Start the bot and get a welcome message. if the user is not in the database, it will be added.
* `/stats` - Get the number of users in the database work only for admin.

**Aiogram**

* Docs: https://docs.aiogram.dev/en/latest/
* Stable version: https://docs.aiogram.dev/en/stable/install.html
* Community: https://t.me/aiogram
* UZ Community: https://t.me/aiogram_uz
* Source code: https://github.com/aiogram/aiogram



