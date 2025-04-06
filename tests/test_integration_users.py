import pytest
from unittest.mock import patch
from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock
from fastapi import FastAPI
from src.database.models import  User

app = FastAPI()

from conftest import test_user


@pytest.fixture
def mock_session():
    mock_session = AsyncMock(spec=AsyncSession)
    return mock_session


@pytest.fixture
def mock_user():
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

