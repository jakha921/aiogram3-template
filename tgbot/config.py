import configparser
from typing import List
from pydantic import BaseModel, Field, validator


class TgBot(BaseModel):
    token: str = Field(..., description="Telegram Bot Token")
    admins_id: List[int] = Field(..., description="List of admin user IDs")
    skip_updates: bool = Field(default=True, description="Skip updates on startup")


class DbConfig(BaseModel):
    host: str = Field(..., description="Database host")
    port: str = Field(..., description="Database port")
    password: str = Field(..., description="Database password")
    user: str = Field(..., description="Database user")
    database: str = Field(..., description="Database name")
    
    @property
    def connection_string(self) -> str:
        """Получить строку подключения к базе данных"""
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class Config(BaseModel):
    tg_bot: TgBot
    db: DbConfig


def cast_str_list(value: str) -> List[int]:
    """Преобразовать строку с ID в список целых чисел"""
    return [int(i.strip()) for i in value.replace(" ", "").split(",") if i.strip()]


def load_config(path: str = '.env') -> Config:
    """Загрузить конфигурацию из файла"""
    config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
    config.read(path)

    # Преобразуем строку с ID админов в список
    admin_ids = cast_str_list(config['tg_bot']['admins_id'])
    
    # Обрабатываем skip_updates с учетом комментариев
    skip_updates_raw = config['tg_bot']['skip_updates']
    # Убираем комментарий и приводим к boolean
    skip_updates = skip_updates_raw.split('#')[0].strip().lower() == 'true'
    
    return Config(
        tg_bot=TgBot(
            token=config['tg_bot']['token'],
            admins_id=admin_ids,
            skip_updates=skip_updates
        ),
        db=DbConfig(
            host=config['db']['host'],
            port=config['db']['port'],
            password=config['db']['password'],
            user=config['db']['user'],
            database=config['db']['database']
        )
    )
