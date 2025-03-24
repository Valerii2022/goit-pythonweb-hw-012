from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date, timedelta
from src.database.db import get_db
from src.database.models import  User
from src.services.auth import  get_current_user
from src.repository.contacts import ContactRepository  
from src.schemas import ContactCreate, ContactUpdate, ContactResponse

router = APIRouter(prefix="/contacts", tags=["contacts"])

@router.get("/search", response_model=List[ContactResponse])
async def search_contacts(
    name: Optional[str] = None,
    surname: Optional[str] = None,
    email: Optional[str] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    contact_repo = ContactRepository(db)
    contacts = await contact_repo.search_contacts(name, surname, email, user)
    return contacts

@router.get("/upcoming-birthdays", response_model=List[ContactResponse])
async def get_upcoming_birthdays(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user),):
    contact_repo = ContactRepository(db)
    today = date.today()
    next_week = today + timedelta(days=7)
    
    return await contact_repo.get_upcoming_birthdays(today, next_week, user)

@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(contact: ContactCreate, db: AsyncSession = Depends(get_db),user: User = Depends(get_current_user),):
    contact_repo = ContactRepository(db) 
    return await contact_repo.create_contact(contact, user)  

@router.get("/", response_model=List[ContactResponse])
async def get_contacts(skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user),):
    contact_repo = ContactRepository(db) 
    return await contact_repo.get_contacts(skip=skip, limit=limit, user=user)  

@router.get("/{contact_id}", response_model=ContactResponse)
async def get_contact_by_id(contact_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user),):
    contact_repo = ContactRepository(db)
    contact = await contact_repo.get_contact_by_id(contact_id=contact_id, user=user)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact

@router.put("/{contact_id}", response_model=ContactResponse)
async def update_contact(contact_id: int, contact: ContactUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user),):
    contact_repo = ContactRepository(db)
    updated_contact = await contact_repo.update_contact(contact_id=contact_id, body=contact, user=user)
    if updated_contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return updated_contact

@router.delete("/{contact_id}", response_model=ContactResponse)
async def delete_contact(contact_id: int, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user),):
    contact_repo = ContactRepository(db)
    contact = await contact_repo.delete_contact(contact_id=contact_id, user=user)
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")
    return contact




