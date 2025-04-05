from datetime import datetime, timedelta, UTC
from typing import Optional

from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from src.database.db import get_db
from src.database.models import User
from src.conf.config import settings
from src.services.users import UserService

import redis
import json

r = redis.Redis(host="localhost", port=6379, password=None)

class Hash:
    """
    Клас для роботи з хешуванням паролів, використовуючи bcrypt.
    """

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password, hashed_password):
        """
        Перевіряє, чи співпадають звичайний та хешований паролі.

        Args:
            plain_password (str): Звичайний пароль.
            hashed_password (str): Хешований пароль.

        Returns:
            bool: True, якщо паролі співпадають, інакше False.
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        """
        Отримує хеш пароля.

        Args:
            password (str): Пароль, який потрібно захешувати.

        Returns:
            str: Хеш пароля.
        """
        return self.pwd_context.hash(password)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

async def create_access_token(data: dict, expires_delta: Optional[int] = None):
    """
    Створює новий JWT токен доступу.

    Args:
        data (dict): Дані для кодування в токені.
        expires_delta (Optional[int]): Час в секундах до закінчення терміну дії токену.

    Returns:
        str: Створений JWT токен.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + timedelta(seconds=expires_delta)
    else:
        expire = datetime.now(UTC) + timedelta(seconds=settings.JWT_EXPIRATION_SECONDS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    """
    Отримує поточного користувача за допомогою токену.

    Args:
        token (str): Токен користувача.
        db (Session): Сесія бази даних.

    Raises:
        HTTPException: Якщо токен недійсний або користувач не знайдений.

    Returns:
        User: Об'єкт користувача.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    cached_user = r.get(token)
    if cached_user is None:
        try:
            payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
            username = payload["sub"]
            if username is None:
                raise credentials_exception
        except JWTError as e:
            raise credentials_exception
        user_service = UserService(db)
        user = await user_service.get_user_by_username(username)
        if user is None:
             raise credentials_exception
        user_data = {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "avatar": user.avatar,
            "confirmed": user.confirmed,}
        r.set(token, json.dumps(user_data))
        r.expire(token, 10)
        return user
    user_data = json.loads(cached_user)
    
    user = User(
        id=user_data["id"],
        username=user_data["username"],
        email=user_data["email"],
        avatar=user_data["avatar"],
        confirmed=user_data["confirmed"]
    )
    
    return user


def create_email_token(data: dict):
    """
    Створює токен для перевірки електронної пошти.

    Args:
        data (dict): Дані для кодування в токені.

    Returns:
        str: Створений JWT токен для перевірки електронної пошти.
    """
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(days=7)
    to_encode.update({"iat": datetime.now(UTC), "exp": expire})
    token = jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)
    return token

async def get_email_from_token(token: str):
    """
    Отримує електронну пошту з токену.

    Args:
        token (str): Токен для отримання електронної пошти.

    Raises:
        HTTPException: Якщо токен недійсний або не вдалось отримати електронну пошту.

    Returns:
        str: Електронна пошта користувача.
    """
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
        )
        email = payload["sub"]
        return email
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Неправильний токен для перевірки електронної пошти",
        )


