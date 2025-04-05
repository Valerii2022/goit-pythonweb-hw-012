from pydantic import BaseModel, ConfigDict, EmailStr
from datetime import date
from typing import Optional

class ContactBase(BaseModel):
    """
    Базова модель для контактної інформації.

    Містить основні поля для контактної інформації: ім'я, прізвище, електронна пошта,
    телефон, дата народження та додаткову інформацію.
    """
    first_name: str
    last_name: str
    email: str
    phone: str
    birth_date: date
    additional_info: Optional[str] = None

class ContactCreate(ContactBase):
    """
    Модель для створення нового контакту.

    Наслідує від `ContactBase` та не містить додаткових полів.
    Використовується для створення нових контактів в базі даних.
    """
    pass

class ContactUpdate(ContactBase):
    """
    Модель для оновлення контактної інформації.

    Всі поля є необов'язковими, щоб дозволити часткове оновлення контактів.
    """
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    birth_date: Optional[date] = None
    additional_info: Optional[str] = None

class Contact(ContactBase):
    """
    Модель для контакту з ідентифікатором.

    Додається поле `id` для унікальної ідентифікації контакту в базі даних.
    """

    id: int

    class Config:
        """
        Конфігурація Pydantic для роботи з ORM.

        Налаштовує Pydantic на роботу з ORM-моделями, де атрибути можуть бути
        отримані з властивостей об'єкта, а не з полів.
        """
        orm_mode = True

class ContactResponse(Contact):
    """
    Модель відповіді на контакт.

    Наслідує від `Contact` і дозволяє відправляти контакти в API як відповідь.
    """
    class Config:
        """
        Конфігурація Pydantic для роботи з ORM.

        Налаштовує Pydantic на роботу з ORM-моделями, де атрибути можуть бути
        отримані з властивостей об'єкта.
        """
        orm_mode = True

class User(BaseModel):
    """
    Модель користувача.

    Містить основні дані користувача: ідентифікатор, ім'я користувача, електронну пошту
    та URL аватара.
    """
    id: int
    username: str
    email: str
    avatar: str

    model_config = ConfigDict(from_attributes=True)

class UserCreate(BaseModel):
    """
    Модель для створення нового користувача.

    Включає необхідні поля для створення користувача: ім'я користувача, електронну пошту
    та пароль.
    """
    username: str
    email: str
    password: str

class Token(BaseModel):
    """
    Модель для токену доступу.

    Містить токен доступу та його тип. Використовується для передачі токенів
    під час аутентифікації.
    """
    access_token: str
    token_type: str

class RequestEmail(BaseModel):
    """
    Модель для запиту на електронну пошту.

    Використовується для прийому електронної пошти при відправці запиту на
    відновлення паролю або інших операцій.
    """
    email: EmailStr

class ChangePasswordRequest(BaseModel):
    """
    Модель для підтвердження відновлення паролю.

    Використовується для підтвердження нового паролю після отримання токену відновлення.
    """
    token: str
    new_password: str
    email: EmailStr