from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar
from sqlalchemy.sql.sqltypes import DateTime
from src.repository.users import UserRepository
from src.schemas import UserCreate

class UserService:
    """
    Сервіс для роботи з користувачами.

    Цей клас забезпечує бізнес-логіку для роботи з користувачами, включаючи створення нових користувачів,
    отримання користувачів за ідентифікатором, іменем або електронною поштою, а також оновлення їх аватарів.
    """

    def __init__(self, db: AsyncSession):
        """
        Ініціалізує сервіс для роботи з користувачами.

        Args:
            db (AsyncSession): Сесія бази даних для асинхронних операцій.
        """
        self.repository = UserRepository(db)

    async def create_user(self, body: UserCreate):
        """
        Створює нового користувача в базі даних.

        Генерує аватар користувача за допомогою Gravatar на основі електронної пошти.
        Якщо не вдається створити аватар, буде встановлено значення `None`.

        Args:
            body (UserCreate): Данні користувача, необхідні для створення нового користувача.

        Returns:
            User: Об'єкт користувача, що був створений у базі даних.
        """
        avatar = None
        try:
            g = Gravatar(body.email)
            avatar = g.get_image()
        except Exception as e:
            print(e)

        return await self.repository.create_user(body, avatar)

    async def get_user_by_id(self, user_id: int):
        """
        Отримує користувача за його ідентифікатором.

        Args:
            user_id (int): Ідентифікатор користувача.

        Returns:
            User: Користувач з вказаним ідентифікатором, або `None`, якщо такий не знайдений.
        """
        return await self.repository.get_user_by_id(user_id)

    async def get_user_by_username(self, username: str):
        """
        Отримує користувача за його ім'ям користувача.

        Args:
            username (str): Ім'я користувача.

        Returns:
            User: Користувач з вказаним іменем, або `None`, якщо такий не знайдений.
        """
        return await self.repository.get_user_by_username(username)

    async def get_user_by_email(self, email: str):
        """
        Отримує користувача за його електронною поштою.

        Args:
            email (str): Електронна пошта користувача.

        Returns:
            User: Користувач з вказаною електронною поштою, або `None`, якщо такий не знайдений.
        """
        return await self.repository.get_user_by_email(email)
    
    async def confirmed_email(self, email: str):
        """
        Перевіряє, чи підтверджена електронна пошта користувача.

        Args:
            email (str): Електронна пошта користувача.

        Returns:
            bool: `True`, якщо електронна пошта підтверджена, `False` інакше.
        """
        return await self.repository.confirmed_email(email)
    
    async def update_avatar_url(self, email: str, url: str):
        """
        Оновлює URL аватара користувача.

        Args:
            email (str): Електронна пошта користувача, для якого оновлюється аватар.
            url (str): Новий URL аватара.

        Returns:
            User: Користувач з оновленим URL аватара.
        """
        return await self.repository.update_avatar_url(email, url)
    
    async def add_reset_password_token_url(self, email: str, password_reset_token: str, password_reset_token_expiry: DateTime):
        """
        Додає token для скидання пароля.

        Args:
            email (str): Електронна пошта користувача, для якого оновлюється аватар.
            password_reset_token(str): token для скидання пароля.
            password_reset_token_expiry(str): Термін дії токена.

        Returns:
            User: Користувач з оновленим token для скидання пароля.
        """
        return await self.repository.add_reset_password_token_url(email, password_reset_token, password_reset_token_expiry)
    
    async def reset_password(self, email: str, newPassword: str):
        """
        Скидання пароля користувача.

        Ця функція викликає метод репозиторію для оновлення пароля користувача в базі даних.

        Args:
            email (str): Електронна адреса користувача, чий пароль потрібно змінити.
            newPassword (str): Новий пароль, який потрібно встановити для користувача.

        Returns:
            bool: Повертає результат виконання операції (True, якщо пароль було успішно змінено, False в іншому випадку).
    
        Raises:
            SomeCustomException: Якщо виникає помилка під час зміни пароля в репозиторії (наприклад, користувач не знайдений).
        """
        return await self.repository.reset_password(email, newPassword)

