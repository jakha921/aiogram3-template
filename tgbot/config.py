import configparser
from dataclasses import dataclass
from typing import List


@dataclass
class TgBot:
    token: str
    admins_id: List[str]
    skip_updates: bool


@dataclass()
class DbConfig:
    host: str
    port: str
    password: str
    user: str
    database: str


@dataclass
class Config:
    tg_bot: TgBot
    db: DbConfig


def cast_str_list(value: str) -> list:
    return [int(i) for i in value.replace(" ", "").split(",")]


def load_config(path: str = '.env') -> Config:
    config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
    config.read(path)

    config = Config(
        tg_bot=TgBot(
            admins_id=cast_str_list(config['tg_bot']['admins_id']),
            **{key: value for key, value in config['tg_bot'].items() if key != 'admins_id'}
        ),
        db=DbConfig(**config['db'])
    )

    return config
