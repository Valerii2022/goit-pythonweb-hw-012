from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import User
from src.schemas import UserCreate

class UserRepository:
    """
    Клас для роботи з репозиторієм користувачів в базі даних.

    Забезпечує доступ до операцій CRUD для таблиці користувачів.
    """

    def __init__(self, session: AsyncSession):
        """
        Ініціалізація репозиторія користувачів.

        Args:
            session (AsyncSession): Сесія для асинхронних запитів до бази даних.
        """
        self.db = session

    async def get_user_by_id(self, user_id: int) -> User | None:
        """
        Отримати користувача за його унікальним ідентифікатором.

        Args:
            user_id (int): Унікальний ідентифікатор користувача.

        Returns:
            User | None: Користувач або None, якщо користувач не знайдений.
        """
        stmt = select(User).filter_by(id=user_id)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> User | None:
        """
        Отримати користувача за його ім'ям користувача.

        Args:
            username (str): Ім'я користувача.

        Returns:
            User | None: Користувач або None, якщо користувач не знайдений.
        """
        stmt = select(User).filter_by(username=username)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> User | None:
        """
        Отримати користувача за його електронною поштою.

        Args:
            email (str): Електронна пошта користувача.

        Returns:
            User | None: Користувач або None, якщо користувач не знайдений.
        """
        stmt = select(User).filter_by(email=email)
        user = await self.db.execute(stmt)
        return user.scalar_one_or_none()

    async def create_user(self, body: UserCreate, avatar: str = None) -> User:
        """
        Створити нового користувача.

        Args:
            body (UserCreate): Дані для створення користувача.
            avatar (str, optional): URL аватару користувача. За замовчуванням None.

        Returns:
            User: Створений користувач.
        """
        user = User(
            **body.model_dump(exclude_unset=True, exclude={"password"}),
            hashed_password=body.password,
            avatar=avatar
        )
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def confirmed_email(self, email: str) -> None:
        """
        Підтвердити електронну пошту користувача.

        Args:
            email (str): Електронна пошта користувача.
        """
        user = await self.get_user_by_email(email)
        user.confirmed = True
        await self.db.commit()

    async def update_avatar_url(self, email: str, url: str) -> User:
        """
        Оновити URL аватару користувача.

        Args:
            email (str): Електронна пошта користувача.
            url (str): Новий URL аватару.

        Returns:
            User: Оновлений користувач з новим аватаром.
        """
        user = await self.get_user_by_email(email)
        user.avatar = url
        await self.db.commit()
        await self.db.refresh(user)
        return user

