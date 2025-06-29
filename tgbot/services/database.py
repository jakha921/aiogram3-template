import aiogram
from typing import AsyncGenerator

import aiomysql
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from tgbot.config import Config
from tgbot.services.db_base import Base


async def create_db_session(config: Config) -> AsyncGenerator[AsyncSession, None]:
    """Create DB session and handle database creation if needed"""

    # Database connection parameters
    auth_data = {
        "user": config.db.user,
        "password": config.db.password,
        "host": config.db.host,
        "port": config.db.port,
        "database": config.db.database,
    }

    print('mysql+aiomysql://{user}:{password}@{host}:{port}/{database}'.format(**auth_data))

    # Check if database exists and create if needed
    try:
        # Подключаемся без выбора БД
        conn = await aiomysql.connect(
            host=auth_data["host"],
            port=int(auth_data["port"]),
            user=auth_data["user"],
            password=auth_data["password"]
        )
        async with conn.cursor() as cur:
            await cur.execute(f"CREATE DATABASE IF NOT EXISTS `{config.db.database}`")
        conn.close()
    except Exception as e:
        print(f"Database initialization error: {e}")
        raise

    # Create async engine
    engine = create_async_engine(
        f"mysql+aiomysql://{auth_data['user']}:{auth_data['password']}@"
        f"{auth_data['host']}:{auth_data['port']}/{auth_data['database']}",
        echo=False,
        future=True,
        pool_pre_ping=False
    )

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session factory
    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    return async_session
