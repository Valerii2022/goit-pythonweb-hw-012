from pathlib import Path
import uuid
from sqlalchemy.orm import Session
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from fastapi import Depends
from pydantic import EmailStr
from datetime import datetime, timedelta
from src.services.auth import create_email_token
from src.services.users import UserService
from src.conf.config import settings
from src.database.db import get_db


# Конфігурація для підключення до поштового сервера
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME=settings.MAIL_FROM_NAME,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=settings.USE_CREDENTIALS,
    VALIDATE_CERTS=settings.VALIDATE_CERTS,
    TEMPLATE_FOLDER=Path(__file__).parent / "templates",
)

async def send_email(email: EmailStr, username: str, host: str):
    """
    Відправляє електронний лист для підтвердження електронної пошти користувача.

    Створює токен для підтвердження електронної пошти та надсилає повідомлення на вказану електронну пошту 
    користувача з шаблоном для підтвердження.

    Args:
        email (EmailStr): Електронна пошта користувача, яку потрібно підтвердити.
        username (str): Ім'я користувача, яке буде використано в шаблоні листа.
        host (str): Хост, який використовується для формування URL для підтвердження електронної пошти.

    Raises:
        ConnectionErrors: Якщо виникає помилка при з'єднанні з поштовим сервером.
    """
    try:
        # Створення токену для підтвердження електронної пошти
        token_verification = create_email_token({"sub": email})
        
        # Підготовка повідомлення для відправки
        message = MessageSchema(
            subject="Confirm your email",
            recipients=[email],
            template_body={
                "host": host,
                "username": username,
                "token": token_verification,
            },
            subtype=MessageType.html,
        )

        # Відправка електронного листа
        fm = FastMail(conf)
        await fm.send_message(message, template_name="verify_email.html")
    except ConnectionErrors as err:
        print(err)

async def send_reset_password_email(email: EmailStr, username: str, db: Session = Depends(get_db),):
    """
    Відправка електронного листа для скидання пароля.

    Ця функція генерує токен скидання пароля, додає його разом з терміном дії до бази даних, 
    а потім надсилає користувачеві email із посиланням на скидання пароля.

    Args:
        email (EmailStr): Електронна адреса користувача, на яку буде надіслано лист.
        username (str): Ім'я користувача, яке буде використано в шаблоні листа.
        db (Session): Сесія бази даних для доступу до інформації про користувачів.

    Returns:
        None: Лист відправляється асинхронно, результат не повертається.

    Raises:
        ConnectionErrors: Якщо виникають помилки під час з'єднання при відправці email.
    """
    try:
        user_service = UserService(db)
        password_reset_token = str(uuid.uuid4().hex[:8])
        password_reset_token_expiry = datetime.now() + timedelta(minutes=5)
        await user_service.add_reset_password_token_url(email, password_reset_token, password_reset_token_expiry)
        
        message = MessageSchema(
            subject="Reset password",
            recipients=[email],
            template_body={
                "username": username,
                "token": password_reset_token,
            },
            subtype=MessageType.html,
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="reset_password_email.html")
    except ConnectionErrors as err:
        print(err)
