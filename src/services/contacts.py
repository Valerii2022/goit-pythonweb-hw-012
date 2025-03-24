from sqlalchemy.ext.asyncio import AsyncSession
from src.repository.contacts import ContactRepository
from src.schemas import ContactCreate, ContactUpdate
from typing import List
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from src.database.models import User

def _handle_integrity_error(e: IntegrityError):
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
    def __init__(self, db: AsyncSession):
        self.repository = ContactRepository(db)

    async def create_contact(self, contact: ContactCreate, user: User):
        try:
            return await self.repository.create_contact(contact, user)
        except IntegrityError as e:
            await self.repository.db.rollback()
            _handle_integrity_error(e)

    async def get_contacts(self, skip: int, limit: int, user: User) -> List:
        return await self.repository.get_contacts(skip, limit, user)

    async def get_contact_by_id(self, contact_id: int, user: User):
        return await self.repository.get_contact_by_id(contact_id, user)

    async def get_contacts_by_name(self, name: str, skip: int, limit: int, user: User) -> List:
        return await self.repository.get_contacts_by_name(name, skip, limit, user)

    async def update_contact(self, contact_id: int, contact_data: ContactUpdate, user: User):
        try:
            return await self.repository.update_contact(contact_id, contact_data, user)
        except IntegrityError as e:
            await self.repository.db.rollback()
            _handle_integrity_error(e)

    async def delete_contact(self, contact_id: int, user: User):
        return await self.repository.delete_contact(contact_id, user)

