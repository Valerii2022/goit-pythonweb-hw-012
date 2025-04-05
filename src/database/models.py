from sqlalchemy import Column, Integer, String, Boolean, func
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.sql.sqltypes import Date, DateTime
from sqlalchemy.sql.schema import ForeignKey

class Base(DeclarativeBase):
    """
    Базовий клас для всіх моделей в SQLAlchemy.
    
    Клас наслідує від `DeclarativeBase`, що дозволяє створювати моделі для таблиць у базі даних.
    """
    pass

class Contact(Base):
    """
    Модель для таблиці `contacts`.
    
    Описує структуру таблиці контактів, що включає персональну інформацію про користувачів, 
    такі як ім'я, прізвище, електронна пошта, телефон, дата народження та інша додаткова інформація.

    Атрибути:
        id (int): Унікальний ідентифікатор контакту.
        first_name (str): Ім'я контакту.
        last_name (str): Прізвище контакту.
        email (str): Електронна пошта контакту.
        phone (str): Телефонний номер контакту.
        birth_date (date): Дата народження контакту.
        additional_info (str): Додаткова інформація про контакт.
        user_id (int): Ідентифікатор користувача, до якого належить контакт (зовнішній ключ).
        user (User): Відношення до користувача, до якого належить цей контакт.
    """
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, index=True, nullable=False)
    last_name = Column(String, index=True, nullable=False)
    email = Column(String, index=True, nullable=False)
    phone = Column(String, nullable=False)
    birth_date = Column(Date, nullable=False)
    additional_info = Column(String, nullable=True)
    user_id = Column(
        "user_id", ForeignKey("users.id", ondelete="CASCADE"), default=None
    )
    user = relationship("User", backref="contacts")

class User(Base):
    """
    Модель для таблиці `users`.
    
    Описує структуру таблиці користувачів, яка містить базову інформацію про користувачів 
    та дані для автентифікації, а також дату створення та можливу аватарку користувача.

    Атрибути:
        id (int): Унікальний ідентифікатор користувача.
        username (str): Ім'я користувача.
        email (str): Електронна пошта користувача.
        hashed_password (str): Захешований пароль користувача.
        created_at (datetime): Дата та час створення користувача.
        avatar (str): URL або шлях до аватарки користувача.
        confirmed (bool): Статус підтвердження користувача.
        role (str): Роль користувача, яка може бути 'user' або 'admin'.
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True)
    email = Column(String, unique=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=func.now())
    avatar = Column(String(255), nullable=True)
    confirmed = Column(Boolean, default=False)
    role = Column(String(10), nullable=False, default="user")


