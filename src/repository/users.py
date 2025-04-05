from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.sqltypes import DateTime
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
    
    async def add_reset_password_token_url(self, email: str, password_reset_token: str, password_reset_token_expiry: DateTime) -> User:
        """
        Додає token для скидання пароля.

        Args:
            email (str): Електронна пошта користувача, для якого оновлюється аватар.
            password_reset_token(str): token для скидання пароля.
            password_reset_token_expiry(str): Термін дії токена.

        Returns:
            User: Користувач з оновленим token для скидання пароля.
        """
        user = await self.get_user_by_email(email)
        user.password_reset_token = password_reset_token
        user.password_reset_token_expiry = password_reset_token_expiry
        await self.db.commit()
        await self.db.refresh(user)
        return user
    
    async def reset_password(self, email: str, newPassword: str) -> User:
        """
        Скидання пароля користувача.

        Ця функція знаходить користувача за електронною поштою, оновлює його пароль, 
        зберігає зміни в базі даних і повертає оновленого користувача.

        Args:
            email (str): Електронна адреса користувача, чий пароль потрібно змінити.
            newPassword (str): Новий пароль, який потрібно встановити для користувача.

        Returns:
            User: Оновлений об'єкт користувача з новим паролем.

        Raises:
            HTTPException: Якщо користувача з такою електронною поштою не знайдено, викидається помилка.
        """
        user = await self.get_user_by_email(email)
        user.hashed_password = newPassword
        await self.db.commit()
        await self.db.refresh(user)
        return user

