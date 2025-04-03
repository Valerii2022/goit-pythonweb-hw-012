import contextlib
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.exc import SQLAlchemyError

from src.conf.config import settings

class DatabaseSessionManager:
    """
    Клас для керування сесіями бази даних.
    
    Використовується для створення асинхронних сесій SQLAlchemy з базою даних
    та автоматичного керування їхнім життєвим циклом.

    Атрибути:
        _engine (AsyncEngine | None): Об'єкт двигуна SQLAlchemy для підключення до бази даних.
        _session_maker (async_sessionmaker): Фабрика сесій для створення сесій.

    Методи:
        session: Асинхронний контекстний менеджер для роботи з сесіями.
    """
    def __init__(self, url: str):
        """
        Ініціалізує менеджер сесій для підключення до бази даних.
        
        Параметри:
            url (str): URL для підключення до бази даних.
        """
        self._engine: AsyncEngine | None = create_async_engine(url)
        
        self._session_maker: async_sessionmaker = async_sessionmaker(
            autoflush=False, autocommit=False, bind=self._engine
        )

    @contextlib.asynccontextmanager
    async def session(self):
        """
        Контекстний менеджер для створення та керування сесією бази даних.
        
        Використовує асинхронний контекст для безпечного створення, використання та закриття сесії.
        
        При виникненні помилки під час роботи з сесією виконується її відкат.
        """
        if self._session_maker is None:
            raise Exception("Database session is not initialized")
        
        session = self._session_maker()
        try:
            yield session  # Повертає сесію для подальшого використання
        except SQLAlchemyError as e:
            await session.rollback()  # Відкат змін при помилці
            raise  # Підвищує помилку для обробки
        finally:
            await session.close()  # Закриває сесію після завершення

# Ініціалізація менеджера сесій для бази даних з використанням URL з конфігурації
sessionmanager = DatabaseSessionManager(settings.DB_URL)

async def get_db():
    """
    Асинхронна функція для отримання сесії бази даних.
    
    Повертає сесію для використання в операціях з базою даних.
    """
    async with sessionmanager.session() as session:
        yield session  # Повертає сесію для виконання запитів

