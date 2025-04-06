import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import asyncio
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from main import app
from src.database.models import Base, User
from src.database.db import get_db
from src.services.auth import create_access_token, Hash


# SQLAlchemy URL бази даних для тестового середовища
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

# Створення асинхронного SQLAlchemy engine для підключення до SQLite бази даних
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Фабрика сесій для створення асинхронних сесій бази даних
TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, expire_on_commit=False, bind=engine
)

# Дані тестового користувача для створення запису в базі даних
test_user = {
    "username": "deadpool",
    "email": "deadpool@example.com",
    "password": "12345678",
}

@pytest.fixture(scope="module", autouse=True)
def init_models_wrap():
    """
    Цей фікстур ініціалізує моделі бази даних для тестування.

    Він створює необхідні таблиці бази даних, додає тестового користувача до 
    бази даних і забезпечує, щоб схема бази даних була налаштована перед виконанням тестів.
    
    Фікстур виконується лише один раз на модуль (згідно з `scope="module"`) і автоматично 
    виконується перед запуском тестів.
    """
    async def init_models():
        # Ініціалізація схеми бази даних: спочатку видаляються всі таблиці, потім створюються нові
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        
        # Додавання тестового користувача до бази даних
        async with TestingSessionLocal() as session:
            hash_password = Hash().get_password_hash(test_user["password"])
            current_user = User(
                username=test_user["username"],
                email=test_user["email"],
                hashed_password=hash_password,
                confirmed=True,
                avatar="<https://twitter.com/gravatar>",
            )
            session.add(current_user)
            await session.commit()

    asyncio.run(init_models())

@pytest.fixture(scope="module")
def client():
    """
    Цей фікстур надає екземпляр TestClient для симуляції HTTP запитів до FastAPI додатку.

    Він перевизначає стандартну залежність `get_db` у додатку, щоб використовувати 
    спеціальну сесію TestingSessionLocal для взаємодії з базою даних, що гарантує, 
    що тести працюватимуть з тестовою базою даних.

    Фікстур виконується один раз на модуль (`scope="module"`).
    """
    async def override_get_db():
        """
        Ця функція перевизначає залежність `get_db` у FastAPI, щоб використовувати 
        тестову сесію бази даних.
        
        Вона надає асинхронну сесію бази даних, яку використовують для виконання тестів.
        """
        async with TestingSessionLocal() as session:
            try:
                yield session
            except Exception as err:
                await session.rollback()
                raise

    # Перевизначення стандартної залежності get_db у додатку FastAPI
    app.dependency_overrides[get_db] = override_get_db

    # Повернення екземпляру TestClient для виконання HTTP запитів під час тестів
    yield TestClient(app)

@pytest_asyncio.fixture()
async def get_token():
    """
    Цей фікстур генерує JWT токен для тестового користувача.

    Він використовує функцію `create_access_token` для генерації токена, 
    який потім повертається для використання в тестах, що потребують авторизації.

    Цей фікстур є асинхронним і надає токен, що відповідає тестовому користувачу `deadpool`.
    """
    token = await create_access_token(data={"sub": test_user["username"]})
    return token


