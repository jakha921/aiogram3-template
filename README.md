# aiogram3_template

### About

---
#### Structure:

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



