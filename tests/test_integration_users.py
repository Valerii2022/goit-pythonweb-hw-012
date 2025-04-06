import pytest
from unittest.mock import patch
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock
from fastapi import FastAPI
from src.database.models import User

app = FastAPI()

from conftest import test_user


@pytest.fixture
def mock_session():
    """
    Фікстура для створення імітованої асинхронної сесії бази даних.
    Повертає об'єкт AsyncMock зі специфікацією AsyncSession.
    """
    mock_session = AsyncMock(spec=AsyncSession)
    return mock_session


@pytest.fixture
def mock_user():
    """
    Фікстура для створення імітованого користувача зі звичайною роллю ("user").
    Повертає екземпляр моделі User з відповідними тестовими даними.
    """
    return User(
        id=1,
        username=test_user["username"],
        email=test_user["email"],
        hashed_password="hash_password",
        confirmed=True,
        avatar="<https://twitter.com/gravatar>",
        role="user",
    )


@pytest.fixture
def mock_admin_user():
    """
    Фікстура для створення імітованого адміністратора (роль "admin").
    Повертає екземпляр моделі User з відповідними тестовими даними.
    """
    return User(
        id=1,
        username=test_user["username"],
        email=test_user["email"],
        hashed_password="hash_password",
        confirmed=True,
        avatar="<https://twitter.com/gravatar>",
        role="admin",
    )


def test_get_me(client, get_token):
    """
    Тест для перевірки ендпоінту отримання інформації про поточного користувача (/api/users/me).

    Перевіряє:
    - Статус код відповіді повинен бути 200.
    - Ім’я користувача та email відповідають тестовим даним.
    - У відповіді присутнє поле 'avatar'.
    """
    token = get_token
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/users/me", headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["username"] == test_user["username"]
    assert data["email"] == test_user["email"]
    assert "avatar" in data


@patch("src.services.upload_file.UploadFileService.upload_file")
def test_update_avatar_user(mock_upload_file, client, get_token):
    """
    Тест для перевірки спроби звичайного користувача змінити аватар (/api/users/avatar).

    Очікувана поведінка:
    - Статус код 403 (доступ заборонено).
    - Відповідь містить повідомлення про відсутність прав.
    - Метод upload_file не викликається.
    """
    fake_url = "<http://example.com/avatar.jpg>"
    mock_upload_file.return_value = fake_url

    headers = {"Authorization": f"Bearer {get_token}"}

    file_data = {"file": ("avatar.jpg", b"fake image content", "image/jpeg")}

    response = client.patch("/api/users/avatar", headers=headers, files=file_data)

    assert response.status_code == 403, response.text

    data = response.json()
    assert "detail" in data
    assert data["detail"] == "У вас немає прав для зміни аватара."  

    mock_upload_file.assert_not_called()
