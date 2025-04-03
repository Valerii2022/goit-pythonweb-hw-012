from sqlalchemy.ext.asyncio import AsyncSession
from src.repository.contacts import ContactRepository
from src.schemas import ContactCreate, ContactUpdate
from typing import List
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from src.database.models import User

def _handle_integrity_error(e: IntegrityError):
    """
    Обробляє помилки цілісності даних, зокрема у випадку порушення унікальності.

    Args:
        e (IntegrityError): Помилка цілісності бази даних.

    Raises:
        HTTPException: У разі порушення унікальності або інших помилок цілісності.
    """
    if "unique_contact_user" in str(e.orig):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Контакт з такою поштою вже існує.",
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Помилка цілісності даних.",
        )

class ContactService:
    """
    Сервіс для роботи з контактами користувача, що включає операції створення, отримання, оновлення та видалення контактів.
    """

    def __init__(self, db: AsyncSession):
        """
        Ініціалізація сервісу контактів.

        Args:
            db (AsyncSession): Асинхронна сесія для роботи з базою даних.
        """
        self.repository = ContactRepository(db)

    async def create_contact(self, contact: ContactCreate, user: User):
        """
        Створює новий контакт для користувача.

        Args:
            contact (ContactCreate): Дані для створення нового контакту.
            user (User): Користувач, для якого створюється контакт.

        Raises:
            HTTPException: Якщо виникла помилка цілісності даних.

        Returns:
            Contact: Створений контакт.
        """
        try:
            return await self.repository.create_contact(contact, user)
        except IntegrityError as e:
            await self.repository.db.rollback()
            _handle_integrity_error(e)

    async def get_contacts(self, skip: int, limit: int, user: User) -> List:
        """
        Отримує список контактів користувача з можливістю пагінації.

        Args:
            skip (int): Кількість контактів, яку потрібно пропустити.
            limit (int): Максимальна кількість контактів для отримання.
            user (User): Користувач, для якого потрібно отримати контакти.

        Returns:
            List: Список контактів.
        """
        return await self.repository.get_contacts(skip, limit, user)

    async def get_contact_by_id(self, contact_id: int, user: User):
        """
        Отримує контакт за його ідентифікатором.

        Args:
            contact_id (int): Ідентифікатор контакту.
            user (User): Користувач, для якого потрібно отримати контакт.

        Returns:
            Contact: Контакт з вказаним ідентифікатором.
        """
        return await self.repository.get_contact_by_id(contact_id, user)

    async def get_contacts_by_name(self, name: str, skip: int, limit: int, user: User) -> List:
        """
        Отримує список контактів за ім'ям з можливістю пагінації.

        Args:
            name (str): Ім'я для пошуку.
            skip (int): Кількість контактів, яку потрібно пропустити.
            limit (int): Максимальна кількість контактів для отримання.
            user (User): Користувач, для якого потрібно отримати контакти.

        Returns:
            List: Список контактів, що відповідають імені.
        """
        return await self.repository.get_contacts_by_name(name, skip, limit, user)

    async def update_contact(self, contact_id: int, contact_data: ContactUpdate, user: User):
        """
        Оновлює контакт користувача за його ідентифікатором.

        Args:
            contact_id (int): Ідентифікатор контакту, що потрібно оновити.
            contact_data (ContactUpdate): Нові дані для контакту.
            user (User): Користувач, для якого оновлюється контакт.

        Raises:
            HTTPException: Якщо виникла помилка цілісності даних.

        Returns:
            Contact: Оновлений контакт.
        """
        try:
            return await self.repository.update_contact(contact_id, contact_data, user)
        except IntegrityError as e:
            await self.repository.db.rollback()
            _handle_integrity_error(e)

    async def delete_contact(self, contact_id: int, user: User):
        """
        Видаляє контакт користувача за його ідентифікатором.

        Args:
            contact_id (int): Ідентифікатор контакту, який потрібно видалити.
            user (User): Користувач, для якого видаляється контакт.

        Returns:
            None
        """
        return await self.repository.delete_contact(contact_id, user)

