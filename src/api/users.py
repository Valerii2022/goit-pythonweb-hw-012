from fastapi import APIRouter, Depends, Request, UploadFile, File, HTTPException, status

from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.schemas import User
from src.conf.config import settings
from src.services.auth import get_current_user
from src.services.users import UserService
from src.services.upload_file import UploadFileService

router = APIRouter(prefix="/users", tags=["users"])
limiter = Limiter(key_func=get_remote_address)

@router.get(
    "/me", response_model=User, description="Не більше 5 запитів на хвилину"
)
@limiter.limit("5/minute")
async def me(request: Request, user: User = Depends(get_current_user)):
    """
    Отримати інформацію про поточного користувача.
    
    Обмеження: не більше 5 запитів на хвилину.
    
    :param request: Об'єкт запиту.
    :param user: Поточний автентифікований користувач.
    :return: Дані користувача.
    """
    return user

@router.patch("/avatar", response_model=User)
async def update_avatar_user(
    file: UploadFile = File(),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Оновити аватар користувача.
    
    :param file: Файл зображення для аватара.
    :param user: Поточний автентифікований користувач.
    :param db: Сесія бази даних.
    :return: Оновлений об'єкт користувача з новим аватаром.
    :raises HTTPException: Якщо користувач не є адміністратором, викидається помилка 403.
    """
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас немає прав для зміни аватара.",
        )
    avatar_url = UploadFileService(
        settings.CLD_NAME, settings.CLD_API_KEY, settings.CLD_API_SECRET
    ).upload_file(file, user.username)

    user_service = UserService(db)
    user = await user_service.update_avatar_url(user.email, avatar_url)

    return user
