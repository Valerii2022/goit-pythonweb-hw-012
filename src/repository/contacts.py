from typing import List, Optional
from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database.models import Contact, User
from src.schemas import ContactCreate, ContactUpdate
from sqlalchemy.sql import extract
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

class ContactRepository:
    """
    Репозиторій для роботи з контактами в базі даних.
    
    Клас надає методи для отримання, створення, оновлення, видалення та пошуку контактів,
    а також для отримання інформації про майбутні дні народження контактів.
    """

    def __init__(self, session: AsyncSession):
        """
        Ініціалізує репозиторій для роботи з контактами.
        
        :param session: Сесія для взаємодії з базою даних.
        """
        self.db = session

    async def get_contacts(self, skip: int, limit: int, user: User) -> List[Contact]:
        """
        Отримує список контактів для вказаного користувача з підтримкою пагінації.
        
        :param skip: Кількість пропущених контактів.
        :param limit: Максимальна кількість контактів для повернення.
        :param user: Користувач, для якого потрібно отримати контакти.
        :return: Список контактів.
        """
        stmt = select(Contact).where(Contact.user_id == user.id).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_contact_by_id(self, contact_id: int, user: User) -> Optional[Contact]:
        """
        Отримує контакт за його ідентифікатором для вказаного користувача.
        
        :param contact_id: Ідентифікатор контакту.
        :param user: Користувач, якому належить контакт.
        :return: Контакт або None, якщо контакт не знайдений.
        """
        stmt = select(Contact).where(Contact.id == contact_id, Contact.user_id == user.id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_contacts_by_name(self, name: str, skip: int, limit: int, user: User) -> List[Contact]:
        """
        Отримує контакти за іменем з підтримкою пагінації.
        
        :param name: Ім'я контакту для пошуку.
        :param skip: Кількість пропущених контактів.
        :param limit: Максимальна кількість контактів для повернення.
        :param user: Користувач, для якого потрібно отримати контакти.
        :return: Список контактів.
        """
        stmt = select(Contact).where(Contact.first_name.ilike(f"%{name}%"), Contact.user_id == user.id).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def create_contact(self, body: ContactCreate, user: User) -> Contact:
        """
        Створює новий контакт для вказаного користувача.
        
        Перевіряє наявність контакту з таким самим email або телефоном, і якщо такий контакт існує,
        генерується помилка.
        
        :param body: Дані для створення нового контакту.
        :param user: Користувач, для якого створюється контакт.
        :return: Створений контакт.
        :raises HTTPException: Якщо контакт з таким email або телефоном уже існує.
        """
        query = select(Contact).where((Contact.user_id == user.id) & ((Contact.email == body.email) | (Contact.phone == body.phone)))
        result = await self.db.execute(query)
        existing_contact = result.scalars().first()

        if existing_contact:
            raise HTTPException(
                status_code=400,
                detail="Ви вже маєте контакт із таким email або телефоном."
            )

        db_contact = Contact(**body.model_dump(exclude_unset=True), user_id=user.id)
        self.db.add(db_contact)

        await self.db.commit()
        await self.db.refresh(db_contact)
        return db_contact

    async def update_contact(self, contact_id: int, body: ContactUpdate, user: User) -> Optional[Contact]:
        """
        Оновлює контакт за його ідентифікатором для вказаного користувача.
        
        :param contact_id: Ідентифікатор контакту, що оновлюється.
        :param body: Нові дані для контакту.
        :param user: Користувач, якому належить контакт.
        :return: Оновлений контакт або None, якщо контакт не знайдений.
        """
        contact = await self.get_contact_by_id(contact_id, user)
        if contact:
            if body.first_name:
                contact.first_name = body.first_name
            if body.last_name:
                contact.last_name = body.last_name
            if body.email:
                contact.email = body.email
            if body.phone:
                contact.phone = body.phone
            if body.birth_date:
                contact.birth_date = body.birth_date
            if body.additional_info:
                contact.additional_info = body.additional_info
            await self.db.commit()
            await self.db.refresh(contact)
        return contact

    async def delete_contact(self, contact_id: int, user: User) -> Optional[Contact]:
        """
        Видаляє контакт за його ідентифікатором для вказаного користувача.
        
        :param contact_id: Ідентифікатор контакту для видалення.
        :param user: Користувач, який хоче видалити контакт.
        :return: Видалений контакт або None, якщо контакт не знайдений.
        """
        contact = await self.get_contact_by_id(contact_id, user)
        if contact:
            await self.db.delete(contact)
            await self.db.commit()
        return contact

    async def search_contacts(self, name: Optional[str], surname: Optional[str], email: Optional[str], user: User):
        """
        Шукає контакти за іменем, прізвищем та email для вказаного користувача.
        
        :param name: Ім'я для пошуку.
        :param surname: Прізвище для пошуку.
        :param email: Email для пошуку.
        :param user: Користувач, для якого потрібно здійснити пошук.
        :return: Список знайдених контактів.
        """
        stmt = select(Contact).where(Contact.user_id == user.id)
        if name:
            stmt = stmt.where(Contact.first_name.ilike(f"%{name}%"))
        if surname:
            stmt = stmt.where(Contact.last_name.ilike(f"%{surname}%"))
        if email:
            stmt = stmt.where(Contact.email.ilike(f"%{email}%"))
        result = await self.db.execute(stmt)
        contacts = result.scalars().all()        
        return contacts
    
    async def get_upcoming_birthdays(self, today: date, next_week: date, user: User):
        """
        Отримує контакти з майбутніми днями народження на основі поточної та наступної дати.
        
        :param today: Поточна дата.
        :param next_week: Дата наступного тижня.
        :param user: Користувач, для якого потрібно отримати контакти з майбутніми днями народження.
        :return: Список контактів з майбутніми днями народження.
        """
        stmt = select(Contact).where(
            (Contact.user_id == user.id) & 
            (
                (
                    (extract('month', Contact.birth_date) == today.month) &
                    (extract('day', Contact.birth_date) >= today.day)
                ) |
                (
                    (extract('month', Contact.birth_date) == next_week.month) &
                    (extract('day', Contact.birth_date) <= next_week.day)
                )
            )
        )

        result = await self.db.execute(stmt)
        return result.scalars().all()

