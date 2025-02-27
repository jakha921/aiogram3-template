from typing import AsyncGenerator

import asyncpg
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

    print('postgres+asyncpg://{user}:{password}@{host}:{port}/{database}'.format(**auth_data))

    # Check if database exists and create if needed
    try:
        conn = await asyncpg.connect(**{**auth_data, "database": "postgres"})
        db_exists = await conn.fetchval(
            "SELECT EXISTS(SELECT 1 FROM pg_database WHERE datname=$1)",
            config.db.database
        )
        if not db_exists:
            await conn.execute(f'CREATE DATABASE "{config.db.database}"')
        await conn.close()
    except Exception as e:
        print(f"Database initialization error: {e}")
        raise

    # Create async engine
    engine = create_async_engine(
        f"postgresql+asyncpg://{auth_data['user']}:{auth_data['password']}@"
        f"{auth_data['host']}:{auth_data['port']}/{auth_data['database']}",
        echo=False,  # Set to True to see SQL queries in the console
        future=True,  # Enable new 2.0 async API
        pool_pre_ping=False  # Check connection health before using
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
