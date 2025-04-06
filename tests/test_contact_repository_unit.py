import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import Contact, User
from src.schemas import ContactBase, ContactUpdate
from datetime import date, timedelta
from unittest.mock import AsyncMock, MagicMock
from src.repository.contacts import ContactRepository
from datetime import datetime, date


@pytest.fixture
def mock_session():
    mock_session = AsyncMock(spec=AsyncSession)
    return mock_session


@pytest.fixture
def contacts_repo(mock_session):
    return ContactRepository(mock_session)


@pytest.fixture
def user():
    user = User(
        id=1,
        username="jo",
        email="jo@example.com",
        hashed_password="12345678",
        created_at=datetime.now(),
        avatar="ava",
        confirmed=False,
        role='user'
    )
    user.contacts = []
    return user


@pytest.mark.asyncio
async def test_get_contacts(contacts_repo, mock_session, user):
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [
        Contact(
            id=1,
            first_name="Alex",
            last_name="Roney",
            email="alex@example.com",
            phone="7107102255",
            birth_date="1988-10-10",
            user_id=user.id,
        )
    ]
    mock_session.execute = AsyncMock(return_value=mock_result)

    contacts = await contacts_repo.get_contacts(skip=0, limit=10, user=user)

    assert len(contacts) == 1
    assert contacts[0].id == 1
    assert contacts[0].first_name == "Alex"

    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_contacts_id(contacts_repo, mock_session, user):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = Contact(
        id=1,
        first_name="Alex",
        last_name="Roney",
        email="alex@example.com",
        phone="7107102255",
        birth_date="1988-10-10",
        user_id=user.id,
    )
    mock_session.execute = AsyncMock(return_value=mock_result)

    contact = await contacts_repo.get_contact_by_id(contact_id=1, user=user)

    assert contact is not None
    assert contact.id == 1
    assert contact.email == "alex@example.com"


@pytest.mark.asyncio
async def test_create_contact(contacts_repo, mock_session, user):
    contact_data = ContactBase(
        first_name="Pat",
        last_name="Roney",
        email="pat@example.com",
        phone="7107102885",
        birth_date=date(1966, 9, 9),
    )
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = None 
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await contacts_repo.create_contact(body=contact_data, user=user)
    
    assert isinstance(result, Contact)
    assert result.first_name == "Pat"
    assert result.last_name == "Roney"
    assert result.email == "pat@example.com"
    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()



@pytest.mark.asyncio
async def test_update_contact(contacts_repo, mock_session, user):
    contact_data = ContactUpdate(first_name="Austin")
    existing_contact = Contact(
        id=1,
        first_name="Alex",
        last_name="Roney",
        email="alex@example.com",
        phone="7107102255",
        birth_date=date(1988, 10, 10),
        user=user,
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_contact
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await contacts_repo.update_contact(
        contact_id=1, body=contact_data, user=user
    )

    assert result is not None
    assert result.first_name == "Austin"
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(existing_contact)


@pytest.mark.asyncio
async def test_remove_contact(contacts_repo, mock_session, user):
    existing_contact = Contact(
        id=1,
        first_name="Alex",
        last_name="Roney",
        email="alex@example.com",
        phone="7107102255",
        birth_date=date(1988, 10, 10),
        user_id=user.id,
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existing_contact
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await contacts_repo.delete_contact(contact_id=1, user=user)

    print(f"Deleting contact: {existing_contact}")
    assert result is not None
    assert result.first_name == "Alex"
    mock_session.delete.assert_awaited_once_with(existing_contact)
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_search_contact_atr(contacts_repo, mock_session, user):
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [
        Contact(
            id=1,
            first_name="Alex",
            last_name="Roney",
            email="alex@example.com",
            phone="7107102255",
            birth_date=date(1988, 10, 10),
            user_id=1,
        ),
        Contact(
            id=2,
            first_name="Jo",
            last_name="Roney",
            email="jo@example.com",
            phone="111556699",
            birth_date=date(1988, 10, 10),
            user_id=2,
        ),
    ]
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await contacts_repo.search_contacts(
        surname="Alex", user=user, name="Roney", email="alex@example.com"
    )

    assert len(result) == 2
    assert result[0].id == 1
    assert result[0].first_name == "Alex"
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_week_birthdays(contacts_repo, mock_session, user):
    start_date = date.today()
    end_date = start_date + timedelta(days=7)
    mock_result = MagicMock()
    mock_result.scalars().all.return_value = [
        Contact(
            id=1,
            first_name="Jo",
            last_name="Roney",
            email="jo@example.com",
            phone="111556699",
            birth_date=start_date + timedelta(days=1),
            user_id=1,
        ),
        Contact(
            id=2,
            first_name="Jo",
            last_name="Roney",
            email="jo@example.com",
            phone="111556699",
            birth_date=end_date,           
            user_id=2,
        ),
    ]
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await contacts_repo.get_upcoming_birthdays(start_date, end_date, user)

    assert len(result) == 2
    assert result[0].birth_date >= start_date and result[0].birth_date <= end_date
    assert result[1].birth_date >= start_date and result[1].birth_date <= end_date

    mock_session.execute.assert_called_once()

