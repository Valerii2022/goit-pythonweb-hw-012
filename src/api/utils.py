from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from src.database.db import get_db

router = APIRouter(tags=["utils"])

@router.get("/healthchecker")
async def healthchecker(db: AsyncSession = Depends(get_db)):
    """
    Перевіряє стан підключення до бази даних.
    
    Виконує тестовий SQL-запит, щоб переконатися, що база даних доступна.
    
    :param db: Сесія бази даних
    :return: Повідомлення про успішне підключення або помилку
    """
    try:
        result = await db.execute(text("SELECT 1"))
        result = result.scalar_one_or_none()

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="База даних налаштована некоректно",
            )
        return {"message": "Ласкаво просимо до FastAPI!"}
    except Exception as e:
        print(e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Помилка підключення до бази даних",
        )
