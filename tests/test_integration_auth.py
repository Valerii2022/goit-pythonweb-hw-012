import pytest
from unittest.mock import Mock, AsyncMock
from sqlalchemy import select
from src.database.models import User
from tests.conftest import TestingSessionLocal
from datetime import datetime, timedelta

user_data = {"username": "agent007", "email": "agent007@gmail.com", "password": "12345678"}


def test_signup(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.api.auth.send_email", mock_send_email)

    response = client.post("api/auth/register", json=user_data)
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert "hashed_password" not in data
    assert "avatar" in data

    response = client.post("api/auth/register", json={})
    assert response.status_code == 422, response.text
    data = response.json()
    assert "detail" in data

    invalid_user_data = {**user_data, "email": "invalid-email"}
    response = client.post("api/auth/register", json=invalid_user_data)

    assert response.status_code == 409, response.text
    data = response.json()
    assert "detail" in data

    invalid_user_data = {**user_data, "password": "123"}
    response = client.post("api/auth/register", json=invalid_user_data)
    assert response.status_code == 409, response.text
    data = response.json()
    assert "detail" in data

    valid_password_user_data = {**user_data, "password": "12345678"}
    response = client.post("api/auth/register", json=valid_password_user_data)
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == "Користувач з таким email вже існує"

    duplicate_user_data = {**user_data, "email": "duplicate-email@gmail.com"}
    response = client.post("api/auth/register", json=duplicate_user_data)
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == "Користувач з таким іменем вже існує"


def test_repeat_signup(client, monkeypatch):
    mock_send_email = Mock()
    monkeypatch.setattr("src.api.auth.send_email", mock_send_email)

    client.post("api/auth/register", json=user_data)

    response = client.post("api/auth/register", json=user_data)
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == "Користувач з таким email вже існує"

def test_not_confirmed_login(client):
    response = client.post("api/auth/login", data={"username": user_data.get("username"), "password": user_data.get("password")})
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Електронна адреса не підтверджена"

@pytest.mark.asyncio
async def test_login(client):
    async with TestingSessionLocal() as session:
        current_user = await session.execute(select(User).where(User.email == user_data.get("email")))
        current_user = current_user.scalar_one_or_none()

    response = client.post("api/auth/login", data={"username": user_data.get("username"), "password": user_data.get("password")})
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Електронна адреса не підтверджена"

    if current_user:
        current_user.confirmed = True
        async with TestingSessionLocal() as session:
            await session.commit()

    response = client.post("api/auth/login", data={"username": user_data.get("username"), "password": user_data.get("password")})
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Електронна адреса не підтверджена"

    response = client.post("api/auth/login", data={"username": user_data.get("username"), "password": "wrongpassword"})
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Неправильний логін або пароль"

    response = client.post("api/auth/login", data={"username": "wrongusername", "password": user_data.get("password")})
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Неправильний логін або пароль"


def test_validation_error_login(client):
    response = client.post("api/auth/login", data={"password": user_data.get("password")})
    assert response.status_code == 422, response.text
    data = response.json()
    assert "detail" in data

    response = client.post("api/auth/login", data={"username": user_data.get("username")})
    assert response.status_code == 422, response.text
    data = response.json()
    assert "detail" in data

def test_confirmed_email(client):
    token = "some_valid_token"
    response = client.get(f"api/auth/confirmed_email/{token}")
    
    if response.status_code == 422:
        assert response.status_code == 422, response.text
        data = response.json()
        assert data["detail"] == "Неправильний токен для перевірки електронної пошти"
    else:
        assert response.status_code == 200, response.text
        data = response.json()
        assert "message" in data
        assert data["message"] == "Електронну пошту підтверджено"

    invalid_token = "invalid_token"
    response = client.get(f"api/auth/confirmed_email/{invalid_token}")
    
    assert response.status_code == 422, response.text
    data = response.json()
    assert data["detail"] == "Неправильний токен для перевірки електронної пошти"  

    response = client.get(f"api/auth/confirmed_email/{token}")
    assert response.status_code == 422, response.text
    data = response.json()
    assert data["detail"] == "Неправильний токен для перевірки електронної пошти"

def test_password_reset_request(client, monkeypatch):
    mock_send_reset_password_email = Mock()
    monkeypatch.setattr("src.api.auth.send_reset_password_email", mock_send_reset_password_email)

    response = client.post("api/auth/password_reset_request", json={"email": user_data["email"]})
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == "Перевірте свою електронну пошту для скидання пароля."

    response = client.post("api/auth/password_reset_request", json={"email": "nonexistent_user@example.com"})
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "Користувача з такою електронною поштою не знайдено."

def test_password_reset(client, monkeypatch):
    mock_reset_password = AsyncMock()
    monkeypatch.setattr("src.api.auth.UserService.reset_password", mock_reset_password)

    mock_get_user_by_email = AsyncMock()
    monkeypatch.setattr("src.api.auth.UserService.get_user_by_email", mock_get_user_by_email)

    mock_user = Mock()
    mock_user.password_reset_token = "valid_reset_token"
    mock_user.password_reset_token_expiry = datetime.now() + timedelta(hours=1)
    mock_get_user_by_email.return_value = mock_user

    reset_data = {
        "email": user_data["email"],
        "token": "valid_reset_token",
        "new_password": "newpassword123"
    }

    response = client.post("api/auth/password_reset", json=reset_data)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == "Пароль успішно змінено!"

    mock_user.password_reset_token = "expired_token"
    mock_user.password_reset_token_expiry = datetime.now() - timedelta(hours=1)
    reset_data["token"] = "expired_token"
    response = client.post("api/auth/password_reset", json=reset_data)
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "Час дії token вийшов."

def test_password_reset_nonexistent_user(client):
    reset_data = {
        "email": "nonexistent_user@example.com",
        "token": "valid_reset_token",
        "new_password": "newpassword123"
    }
    response = client.post("api/auth/password_reset", json=reset_data)
    assert response.status_code == 404, response.text
    data = response.json()
    assert data["detail"] == "Користувача з такою електронною поштою не знайдено."

