from fastapi import APIRouter, HTTPException, Depends, status, BackgroundTasks, Request
from sqlalchemy.orm import Session
from datetime import datetime
from fastapi.security import OAuth2PasswordRequestForm
from src.schemas import UserCreate, Token, UserBase, RequestEmail, ChangePasswordRequest
from src.services.auth import create_access_token, Hash, get_email_from_token
from src.services.users import UserService
from src.database.db import get_db
from src.services.email import send_email, send_reset_password_email

# Ініціалізація роутера для автентифікації
router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register", response_model=UserBase, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Реєстрація нового користувача.
    
    Args:
        user_data (UserCreate): Дані користувача для реєстрації.
        background_tasks (BackgroundTasks): Фонова задача для відправлення email.
        request (Request): HTTP-запит.
        db (Session): Сесія бази даних.

    Returns:
        User: Створений користувач.
    """
    user_service = UserService(db)

    email_user = await user_service.get_user_by_email(user_data.email)
    if email_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Користувач з таким email вже існує",
        )

    username_user = await user_service.get_user_by_username(user_data.username)
    if username_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Користувач з таким іменем вже існує",
        )
    user_data.password = Hash().get_password_hash(user_data.password)
    new_user = await user_service.create_user(user_data)
    background_tasks.add_task(
        send_email, new_user.email, new_user.username, request.base_url
    )
    return new_user

@router.post("/login", response_model=Token)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
):
    """
    Вхід користувача в систему.
    
    Args:
        form_data (OAuth2PasswordRequestForm): Дані для входу.
        db (Session): Сесія бази даних.

    Returns:
        dict: Токен доступу.
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_username(form_data.username)
    if not user or not Hash().verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неправильний логін або пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Електронна адреса не підтверджена",
        )
    access_token = await create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/confirmed_email/{token}")
async def confirmed_email(token: str, db: Session = Depends(get_db)):
    """
    Підтвердження електронної пошти користувача.
    
    Args:
        token (str): Токен підтвердження.
        db (Session): Сесія бази даних.

    Returns:
        dict: Повідомлення про підтвердження пошти.
    """
    email = await get_email_from_token(token)
    user_service = UserService(db)
    user = await user_service.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.confirmed:
        return {"message": "Ваша електронна пошта вже підтверджена"}
    await user_service.confirmed_email(email)
    return {"message": "Електронну пошту підтверджено"}

@router.post("/request_email")
async def request_email(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Запит на повторне підтвердження електронної пошти.
    
    Args:
        body (RequestEmail): Електронна адреса для підтвердження.
        background_tasks (BackgroundTasks): Фонова задача для відправлення email.
        request (Request): HTTP-запит.
        db (Session): Сесія бази даних.

    Returns:
        dict: Повідомлення про статус запиту.
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_email(body.email)

    if user.confirmed:
        return {"message": "Ваша електронна пошта вже підтверджена"}
    if user:
        background_tasks.add_task(
            send_email, user.email, user.username, request.base_url
        )
    return {"message": "Перевірте свою електронну пошту для підтвердження"}

@router.post("/password_reset_request")
async def request_email(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Запит на скидання пароля для користувача.

    Цей маршрут ініціює процес скидання пароля та надсилає електронний лист із посиланням для скидання пароля.
    Якщо користувач з вказаною електронною поштою не знайдений, буде викинута помилка 404.

    Args:
        body (RequestEmail): Тіло запиту, що містить електронну пошту користувача.
        background_tasks (BackgroundTasks): Фонова задача для відправлення email.
        db (Session): Сесія бази даних для доступу до інформації про користувачів.

    Returns:
        dict: Повідомлення про успішну відправку запиту на скидання пароля.
    
    Raises:
        HTTPException: Якщо користувача з такою електронною поштою не знайдено (404).
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_email(body.email)

    if not user:
        raise HTTPException(status_code=404, detail="Користувача з такою електронною поштою не знайдено.")
    background_tasks.add_task(
        send_reset_password_email, user.email, user.username, db
    )

    return {"message": "Перевірте свою електронну пошту для скидання пароля."}

@router.post("/password_reset")
async def request_email(
    body: ChangePasswordRequest,
    db: Session = Depends(get_db),
):
    """
    Запит на зміну пароля користувача через токен скидання пароля.

    Цей маршрут дозволяє користувачеві змінити пароль за допомогою токена скидання пароля. Якщо токен неправильний
    або час його дії минув, викидається відповідна помилка. Пароль зберігається після хешування.

    Args:
        body (ChangePasswordRequest): Тіло запиту, що містить електронну пошту, новий пароль та токен скидання.
        db (Session): Сесія бази даних для доступу до користувачів.

    Returns:
        dict: Повідомлення про успішну зміну пароля.
    
    Raises:
        HTTPException: Якщо користувача з такою електронною поштою не знайдено (404).
        HTTPException: Якщо токен скидання пароля неправильний (404).
        HTTPException: Якщо токен скидання пароля прострочений (404).
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_email(body.email)
    current_time = datetime.now()

    if not user:
        raise HTTPException(status_code=404, detail="Користувача з такою електронною поштою не знайдено.")
    if user.password_reset_token != body.token:
        raise HTTPException(status_code=404, detail="Невірний token скидання пароля.")
    if user.password_reset_token_expiry < current_time:
        raise HTTPException(status_code=404, detail="Час дії token вийшов.")
    new_password = Hash().get_password_hash(body.new_password)
    await user_service.reset_password(body.email, new_password)
    
    return {"message": "Пароль успішно змінено!"}