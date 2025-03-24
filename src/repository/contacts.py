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
    def __init__(self, session: AsyncSession):
        self.db = session

    async def get_contacts(self, skip: int, limit: int, user: User) -> List[Contact]:
        stmt = select(Contact).where(Contact.user_id == user.id).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_contact_by_id(self, contact_id: int, user: User) -> Optional[Contact]:
        stmt = select(Contact).where(Contact.id == contact_id, Contact.user_id == user.id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_contacts_by_name(self, name: str, skip: int, limit: int, user: User) -> List[Contact]:
        stmt = select(Contact).where(Contact.first_name.ilike(f"%{name}%"), Contact.user_id == user.id).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def create_contact(self, body: ContactCreate, user: User) -> Contact:
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
        contact = await self.get_contact_by_id(contact_id, user)
        if contact:
            await self.db.delete(contact)
            await self.db.commit()
        return contact

    async def search_contacts(self, name: Optional[str], surname: Optional[str], email: Optional[str], user: User):
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

