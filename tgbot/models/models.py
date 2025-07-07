from sqlalchemy import Column, BigInteger, String, select, func, insert, update, literal_column, text, case
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

    # get user invoice eby phone number and chosen month
    @classmethod
    async def get_user_invoice(cls, db_session: sessionmaker, phone: str, month: str):
        """
        Get user invoice by phone number and chosen month

        SELECT
            o.obj_name AS "Магазин/Склад",
            g.gd_code AS "Код",
            g.gd_name AS "Номенклатура",
            s.sls_datetime AS "Дата/Время",
            'Продажа' AS "Тип",
            op.opr_quantity AS "Количество",
            a.oap_price1 AS "Цена",
            (op.opr_quantity * a.oap_price1) AS "Сумма",
            dss.sords_name AS "Статус оплаты"
        FROM doc_sales s
        JOIN operations op
            ON op.opr_document = s.sls_id AND op.opr_type = 2
        JOIN operations_additional_prop a
            ON a.oap_operation = op.opr_id
        JOIN dir_goods g
            ON g.gd_id = op.opr_good
        JOIN dir_objects o
            ON o.obj_id = s.sls_object
        JOIN dir_customers c
            ON c.cstm_id = s.sls_customer
        JOIN dir_sales_status dss
            ON dss.sords_id = s.sls_status
        WHERE s.sls_datetime BETWEEN '2015-01-01' AND '2044-06-15'
            AND s.sls_performed = 1
            AND s.sls_deleted = 0
            AND %s IN (c.cstm_phone, c.cstm_phone2, c.cstm_phone3, c.cstm_phone4)
            AND dss.sords_name != 'Завершен'
            AND EXTRACT(MONTH FROM s.sls_datetime) = %s"
            ORDER BY s.sls_datetime DESC
        """
        async with db_session() as session:
            stmt = select(
                literal_column("o.obj_name").label("Магазин/Склад"),
                literal_column("g.gd_code").label("Код"),
                literal_column("g.gd_name").label("Номенклатура"),
                literal_column("s.sls_datetime").label("Дата/Время"),
                literal_column("'Продажа'").label("Тип"),
                literal_column("op.opr_quantity").label("Количество"),
                literal_column("a.oap_price1").label("Цена"),
                (literal_column("op.opr_quantity") * literal_column("a.oap_price1")).label("Сумма"),
                literal_column("dss.sords_name").label("Статус оплаты")
            ).select_from(
                text(
                    "doc_sales s "
                    "JOIN operations op ON op.opr_document = s.sls_id AND op.opr_type = 2 "
                    "JOIN operations_additional_prop a ON a.oap_operation = op.opr_id "
                    "JOIN dir_goods g ON g.gd_id = op.opr_good "
                    "JOIN dir_objects o ON o.obj_id = s.sls_object "
                    "JOIN dir_customers c ON c.cstm_id = s.sls_customer "
                    "JOIN dir_sales_status dss ON dss.sords_id = s.sls_status"
                )
            ).where(
                text("s.sls_datetime BETWEEN '2015-01-01' AND '2044-06-15'"),
                text("s.sls_performed = 1"),
                text("s.sls_deleted = 0"),
                text(":phone IN (c.cstm_phone, c.cstm_phone2, c.cstm_phone3, c.cstm_phone4)"),
                text("dss.sords_name != 'Завершен'"),
                text("EXTRACT(MONTH FROM s.sls_datetime) = :month")
            ).order_by(text("s.sls_datetime DESC"))
            result = await session.execute(stmt, {"phone": phone, "month": month})
            return result.fetchall()

    @classmethod
    async def get_all_sales_invoices_summary(cls, db_session: sessionmaker, year: int = None, month: int = None):
        """
        Retrieves a summary of all sales invoices from the database with optional filtering.
        Оптимизированная версия с фильтрацией на уровне БД.

        Args:
            db_session: The SQLAlchemy sessionmaker object for database interaction.
            year: Optional year filter
            month: Optional month filter

        Returns:
            A list of dictionaries, where each dictionary represents a row from the
            query result, containing the summarized sales invoice data.
        """
        async with db_session() as session:
            # Базовые условия WHERE
            where_conditions = [
                text("s.sls_performed = 1"),
                text("s.sls_deleted = 0")
            ]
            
            # Добавляем фильтры по году и месяцу если переданы
            if year is not None:
                where_conditions.append(text("EXTRACT(YEAR FROM s.sls_datetime) = :year"))
            if month is not None:
                where_conditions.append(text("EXTRACT(MONTH FROM s.sls_datetime) = :month"))
            
            stmt = select(
                literal_column("s.sls_id").label("Код"),
                literal_column("s.sls_datetime").label("Дата/время"),
                literal_column("'Продажа'").label("Тип операции"),
                literal_column("o.obj_name").label("Магазин/Склад"),
                literal_column("dss.sords_name").label("Статус документа"),
                literal_column("c.cstm_name").label("Покупатель"),
                func.sum(literal_column("op.opr_quantity") * literal_column("a.oap_price1")).label("Сумма продажи")
            ).select_from(
                text(
                    "doc_sales AS s "
                    "JOIN dir_objects AS o ON s.sls_object = o.obj_id "
                    "JOIN dir_sales_status AS dss ON s.sls_status = dss.sords_id "
                    "JOIN dir_customers AS c ON s.sls_customer = c.cstm_id "
                    "JOIN operations AS op ON op.opr_document = s.sls_id AND op.opr_type = 2 "
                    "JOIN operations_additional_prop AS a ON a.oap_operation = op.opr_id"
                )
            ).where(
                *where_conditions
            ).group_by(
                text("s.sls_id"),
                text("s.sls_datetime"),
                text("o.obj_name"),
                text("dss.sords_name"),
                text("c.cstm_name")
            ).order_by(
                text("s.sls_datetime DESC"),
                text("s.sls_id DESC")
            )
            
            # Параметры для фильтров
            params = {}
            if year is not None:
                params["year"] = year
            if month is not None:
                params["month"] = month
            
            result = await session.execute(stmt, params)
            # Fetch all results and convert rows to dictionaries for easier consumption
            return [row._asdict() for row in result.fetchall()]
    
    @classmethod
    async def get_sales_invoices_by_period(cls, db_session: sessionmaker, year: int, month: int):
        """
        Получить накладные за конкретный период (оптимизированная версия)
        """
        return await cls.get_all_sales_invoices_summary(db_session, year=year, month=month)
    
    @classmethod
    async def get_sales_document_details(cls, db_session: sessionmaker, sales_id: int):
        """
        Retrieves detailed line-item information for a specific sales document.

        This method fetches the goods code, item name, quantity, price per unit,
        total sum per item, store/warehouse name, date/time of the sale, and
        the sales document ID for a given sales document.

        Args:
            db_session: The SQLAlchemy sessionmaker object for database interaction.
            sales_id: The ID of the sales document to retrieve details for.

        Returns:
            A list of dictionaries, where each dictionary represents a row from the
            query result, containing the detailed sales document data.
        """
        async with db_session() as session:
            stmt = select(
                literal_column("g.gd_code").label("Код товара"),
                literal_column("g.gd_name").label("Наименование"),
                literal_column("op.opr_quantity").label("Количество"),
                literal_column("a.oap_price1").label("Цена"),
                (literal_column("op.opr_quantity") * literal_column("a.oap_price1")).label("Сумма"),
                literal_column("o.obj_name").label("Магазин/Склад"),
                literal_column("s.sls_datetime").label("Дата/Время"),
                literal_column("s.sls_id").label("ID Док")
            ).select_from(
                text(
                    "doc_sales AS s "
                    "JOIN operations AS op ON op.opr_document = s.sls_id AND op.opr_type = 2 "
                    "JOIN operations_additional_prop AS a ON a.oap_operation = op.opr_id "
                    "JOIN dir_goods AS g ON g.gd_id = op.opr_good "
                    "JOIN dir_objects AS o ON s.sls_object = o.obj_id"
                )
            ).where(
                text("s.sls_id = :sales_id"),
                text("s.sls_performed = 1"),
                text("s.sls_deleted = 0")
            ).order_by(
                text("op.opr_id")
            )

            result = await session.execute(stmt, {"sales_id": sales_id})
            # Fetch all results and convert rows to dictionaries for easier consumption
            return [row._asdict() for row in result.fetchall()]
    
    
    @classmethod
    async def get_customer_sales_summary(cls, db_session: sessionmaker, phone_number: str, year: int = None, month: int = None):
        """
        Retrieves a summary of sales for a given customer phone number,
        including the total sales amount, paid amount, and remaining debt.
        Фильтрует по году и месяцу, если переданы.
        """
        async with db_session() as session:
            sales_sum_col = func.coalesce(
                func.sum(literal_column("op.opr_quantity") * literal_column("a.oap_price1")),
                0
            ).label("Сумма")
            paid_sum_col = func.coalesce(
                func.sum(
                    case(
                        (literal_column("dco.cop_type").in_([1, 4]), literal_column("dco.cop_value")),
                        else_=0
                    )
                ),
                0
            ).label("Оплачено")

            where_clauses = [
                text(
                    "c.cstm_phone = :phone_number OR "
                    "c.cstm_phone2 = :phone_number OR "
                    "c.cstm_phone3 = :phone_number OR "
                    "c.cstm_phone4 = :phone_number"
                ),
                text("s.sls_performed = 1"),
                text("s.sls_deleted = 0")
            ]
            if year:
                where_clauses.append(text("EXTRACT(YEAR FROM s.sls_datetime) = :year"))
            if month:
                where_clauses.append(text("EXTRACT(MONTH FROM s.sls_datetime) = :month"))

            stmt = select(
                literal_column("s.sls_datetime").label("Дата"),
                func.concat(literal_column("'Реализация №'"), literal_column("s.sls_id")).label("Документ"),
                sales_sum_col,
                paid_sum_col,
                (sales_sum_col - paid_sum_col).label("Долг"),
                literal_column("s.sls_note").label("Примечание")
            ).select_from(
                text(
                    "doc_sales AS s "
                    "LEFT JOIN operations AS op ON op.opr_document = s.sls_id AND op.opr_type = 2 "
                    "LEFT JOIN operations_additional_prop AS a ON a.oap_operation = op.opr_id "
                    "LEFT JOIN doc_cash_operations AS dco ON dco.cop_payment = s.sls_id "
                    "JOIN dir_customers AS c ON s.sls_customer = c.cstm_id"
                )
            ).where(
                *where_clauses
            ).group_by(
                text("s.sls_id"),
                text("s.sls_datetime"),
                text("s.sls_note")
            ).order_by(
                text("s.sls_datetime DESC"),
                text("s.sls_id DESC")
            )

            params = {"phone_number": phone_number}
            if year:
                params["year"] = year
            if month:
                params["month"] = month

            result = await session.execute(stmt, params)
            return [row._asdict() for row in result.fetchall()]

    @classmethod
    async def get_sales_years(cls, db_session: sessionmaker):
        """
        Получить список уникальных годов, в которых были продажи.
        """
        async with db_session() as session:
            stmt = select(func.extract('year', literal_column('sls_datetime')).label('year')).select_from(text('doc_sales')).where(
                text('sls_performed = 1'),
                text('sls_deleted = 0')
            ).group_by(text('year')).order_by(text('year DESC'))
            result = await session.execute(stmt)
            return [int(row.year) for row in result.fetchall() if row.year]

    @classmethod
    async def get_sales_months(cls, db_session: sessionmaker, year: int):
        """
        Получить список уникальных месяцев, в которых были продажи за указанный год.
        """
        async with db_session() as session:
            stmt = select(func.extract('month', literal_column('sls_datetime')).label('month')).select_from(text('doc_sales')).where(
                text('sls_performed = 1'),
                text('sls_deleted = 0'),
                text('EXTRACT(YEAR FROM sls_datetime) = :year')
            ).group_by(text('month')).order_by(text('month'))
            result = await session.execute(stmt, {'year': year})
            return [int(row.month) for row in result.fetchall() if row.month]

    @classmethod
    async def get_customers_by_period(cls, db_session: sessionmaker, year: int, month: int = None):
        """
        Получить список покупателей, у которых были продажи за указанный год и (опционально) месяц.
        """
        async with db_session() as session:
            where_clauses = [
                text('s.sls_performed = 1'),
                text('s.sls_deleted = 0'),
                text('EXTRACT(YEAR FROM s.sls_datetime) = :year')
            ]
            params = {'year': year}
            if month:
                where_clauses.append(text('EXTRACT(MONTH FROM s.sls_datetime) = :month'))
                params['month'] = month
            stmt = select(
                literal_column('c.cstm_id').label('id'),
                literal_column('c.cstm_name').label('name'),
                literal_column('c.cstm_phone').label('phone')
            ).select_from(
                text('doc_sales AS s JOIN dir_customers AS c ON s.sls_customer = c.cstm_id')
            ).where(
                *where_clauses
            ).group_by(
                text('c.cstm_id'),
                text('c.cstm_name'),
                text('c.cstm_phone')
            ).order_by(text('c.cstm_name'))
            result = await session.execute(stmt, params)
            return [row._asdict() for row in result.fetchall()]

    @classmethod
    async def get_customer_name_by_phone(cls, db_session: sessionmaker, phone_number: str):
        """
        Получить название покупателя по номеру телефона.
        """
        async with db_session() as session:
            stmt = select(
                literal_column('c.cstm_name').label('name')
            ).select_from(
                text('dir_customers AS c')
            ).where(
                text(
                    "c.cstm_phone = :phone_number OR "
                    "c.cstm_phone2 = :phone_number OR "
                    "c.cstm_phone3 = :phone_number OR "
                    "c.cstm_phone4 = :phone_number"
                )
            ).limit(1)
            
            result = await session.execute(stmt, {"phone_number": phone_number})
            row = result.fetchone()
            return row.name if row else phone_number