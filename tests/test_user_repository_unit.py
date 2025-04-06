import pytest
from src.database.models import User
from src.schemas import UserCreate
from sqlalchemy.ext.asyncio import AsyncSession

from unittest.mock import AsyncMock, MagicMock
from src.repository.users import UserRepository
from datetime import datetime


@pytest.fixture
def mock_session():
    """
    Фікстура для створення імітованої асинхронної сесії SQLAlchemy.
    """
    mock_session = AsyncMock(spec=AsyncSession)
    return mock_session


@pytest.fixture
def user_repo(mock_session):
    """
    Фікстура для створення екземпляра UserRepository з імітованою сесією.
    """
    return UserRepository(mock_session)


@pytest.mark.asyncio
async def test_get_user_by_id(user_repo, mock_session):
    """
    Перевіряє правильність отримання користувача за ID.
    """
    mock_user = User(
        id=1,
        username="some_user",
        email="some_user@gmail.com",
        hashed_password="pass_with_hash_logic",
        created_at=datetime(2025, 2, 2, 11, 0, 0),
        avatar="ava",
        confirmed=True,
        role='user',
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await user_repo.get_user_by_id(mock_user.id)

    assert result == mock_user
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_by_name(user_repo, mock_session):
    """
    Перевіряє правильність отримання користувача за іменем користувача (username).
    """
    mock_user = User(
        id=1,
        username="some_user",
        email="some_user@gmail.com",
        hashed_password="pass_with_hash_logic",
        created_at=datetime(2025, 2, 2, 11, 0, 0),
        avatar="ava",
        confirmed=True,
        role='user',
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await user_repo.get_user_by_username(mock_user.username)

    assert result == mock_user
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_user_by_email(user_repo, mock_session):
    """
    Перевіряє правильність отримання користувача за електронною поштою.
    """
    mock_user = User(
        id=1,
        username="some_user",
        email="some_user@gmail.com",
        hashed_password="pass_with_hash_logic",
        created_at=datetime(2025, 2, 2, 11, 0, 0),
        avatar="ava",
        confirmed=True,
        role='user',
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_user
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await user_repo.get_user_by_email(mock_user.email)

    assert result == mock_user
    mock_session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_create_user(user_repo, mock_session):
    """
    Перевіряє створення нового користувача на основі переданих даних.
    """
    user_data = UserCreate(
        username="test_user", email="test@gamil.com", password="test_pass"
    )
    mock_session.add = AsyncMock()
    mock_session.commit = AsyncMock()
    mock_session.refresh = AsyncMock()

    result = await user_repo.create_user(body=user_data)

    assert isinstance(result, User)
    assert result.username == "test_user"
    mock_session.add.assert_called_once()
    mock_session.add.assert_called_once_with(result)
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(result)


@pytest.mark.asyncio
async def test_update_user(user_repo, mock_session):
    """
    Перевіряє оновлення аватарки користувача за його електронною поштою.
    """
    email = "some_user@gmail.com"
    new_avatar_url = "new_ava"

    existed_user = User(
        id=1,
        username="some_user",
        email=email,
        hashed_password="pass_with_hash_logic",
        created_at=datetime(2025, 2, 2, 11, 0, 0),
        avatar="ava",
        confirmed=True,
        role='admin',
    )
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = existed_user
    mock_session.execute = AsyncMock(return_value=mock_result)
    
    result = await user_repo.update_avatar_url(email=email, url=new_avatar_url)

    assert result is not None
    assert result.avatar == new_avatar_url
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(result)


@pytest.mark.asyncio
async def test_confirmed_email(user_repo, mock_session):
    """
    Перевіряє підтвердження електронної пошти користувача.
    """
    email = "test_email"
    existing_user = User(
        id=1,
        username="some_user",
        email="some_user@gmail.com",
        hashed_password="pass_with_hash_logic",
        created_at=datetime(2025, 2, 2, 11, 0, 0),
        avatar="ava",
        confirmed=False,  
        role='user',
    )
    user_repo.get_user_by_email = AsyncMock(return_value=existing_user)
    mock_session.commit = AsyncMock()
    user_repo.db = mock_session
    await user_repo.confirmed_email(email)
    assert existing_user.confirmed is True 
    mock_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_add_reset_password_token_url(user_repo, mock_session):
    """
    Перевіряє додавання токена для скидання пароля та терміну його дії.
    """
    email = "user@example.com"
    password_reset_token = "random_reset_token"
    password_reset_token_expiry = datetime(2025, 12, 31, 23, 59, 59)
    
    existing_user = User(
        id=1,
        username="test_user",
        email=email,
        hashed_password="old_password_hash",
        created_at=datetime(2025, 2, 2, 11, 0, 0),
        avatar="ava",
        confirmed=True,
        role='user',
        password_reset_token=None,
        password_reset_token_expiry=None,
    )
    user_repo.get_user_by_email = AsyncMock(return_value=existing_user)
    mock_session.commit = AsyncMock()
    user_repo.db = mock_session

    updated_user = await user_repo.add_reset_password_token_url(
        email=email,
        password_reset_token=password_reset_token,
        password_reset_token_expiry=password_reset_token_expiry
    )

    assert updated_user.password_reset_token == password_reset_token
    assert updated_user.password_reset_token_expiry == password_reset_token_expiry
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(updated_user)


@pytest.mark.asyncio
async def test_reset_password(user_repo, mock_session):
    """
    Перевіряє функціонал скидання пароля для користувача.
    """
    email = "user@example.com"
    new_password = "new_secure_password"
    
    existing_user = User(
        id=1,
        username="test_user",
        email=email,
        hashed_password="old_password_hash",
        created_at=datetime(2025, 2, 2, 11, 0, 0),
        avatar="ava",
        confirmed=True,
        role='user',
        password_reset_token="some_token",
        password_reset_token_expiry=datetime(2025, 12, 31, 23, 59, 59),
    )
    user_repo.get_user_by_email = AsyncMock(return_value=existing_user)
    mock_session.commit = AsyncMock()
    user_repo.db = mock_session
    updated_user = await user_repo.reset_password(email=email, newPassword=new_password)

    assert updated_user.hashed_password == new_password
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once_with(updated_user)

