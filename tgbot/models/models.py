from sqlalchemy import Column, BigInteger, String, select, func, insert, update
from sqlalchemy.orm import sessionmaker

from tgbot.services.db_base import Base


class TGUser(Base):
    __tablename__ = "telegram_users"
    telegram_id = Column(BigInteger, unique=True, primary_key=True)
    firstname = Column(String(length=100))
    lastname = Column(String(length=100))
    username = Column(String(length=100), nullable=True)
    phone = Column(String(length=15), nullable=True)
    lang_code = Column(String(length=10), default='en')

    def __repr__(self):
        return f"<TGUser {self.firstname} {self.lastname}>"

    @classmethod
    async def get_user(cls, db_session: sessionmaker, telegram_id: int) -> 'TGUser':
        """
        Get user by telegram_id

        SELECT * FROM telegram_users WHERE telegram_id = :telegram_id;
        """
        async with db_session() as session:
            sql = select(cls).where(cls.telegram_id == telegram_id)
            user = await session.execute(sql)
            return user.scalar_one_or_none()

    @classmethod
    async def add_user(cls, db_session: sessionmaker, telegram_id: int, firstname: str, lastname: str,
                       username: str = None,
                       phone: str = None, lang_code: str = None):
        """
        Add new user into DB

        INSERT INTO telegram_users (telegram_id, firstname, lastname, username, phone, lang_code)
        """
        async with db_session() as session:
            values = {
                'telegram_id': telegram_id,
                'firstname': firstname,
                'lastname': lastname,
                'username': username,
                'phone': phone,
                'lang_code': lang_code,
            }
            sql = insert(cls).values(**values)
            result = await session.execute(sql)
            await session.commit()
            return result

    @classmethod
    async def update_user(cls, db_session: sessionmaker, telegram_id: int, **kwargs):
        """
        Update user by telegram_id

        UPDATE telegram_users SET key1=value1, key2=value2 WHERE telegram_id = :telegram_id;
        """
        async with db_session() as session:
            sql = update(cls).where(cls.telegram_id == telegram_id).values(**kwargs)
            result = await session.execute(sql)
            await session.commit()
            return result

    @classmethod
    async def get_all_users(cls, db_session: sessionmaker):
        """
        Get all users

        SELECT * FROM telegram_users;
        """
        async with db_session() as session:
            sql = select(cls)
            result = await session.execute(sql)
            users: list = result.fetchall()
        return users

    @classmethod
    async def get_users_count(cls, db_session: sessionmaker) -> int:
        """
        Get count of users

        SELECT COUNT(telegram_id) FROM telegram_users;
        """
        async with db_session() as session:
            sql = select(func.count(cls.telegram_id))
            result = await session.execute(sql)
            return result.scalar()

    @classmethod
    async def get_user_by_filter(cls, db_session: sessionmaker, **kwargs):
        async with db_session() as session:
            sql = select(cls).where(**kwargs)
            user = await session.execute(sql)
            return user.scalar_one_or_none()