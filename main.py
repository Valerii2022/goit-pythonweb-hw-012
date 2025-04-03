from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from src.api import utils, contacts, auth, users

# Ініціалізація FastAPI додатку
app = FastAPI()

# Визначення дозволених джерел для CORS
origins = [
    "<http://localhost:3000>"
]

# Додавання проміжного програмного забезпечення CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """
    Обробник винятків для перевищення ліміту запитів.
    
    Args:
        request (Request): Вхідний HTTP-запит.
        exc (RateLimitExceeded): Виняток, що виникає при перевищенні ліміту запитів.

    Returns:
        JSONResponse: Відповідь із кодом 429 (занадто багато запитів).
    """
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"error": "Перевищено ліміт запитів. Спробуйте пізніше."},
    )

# Підключення роутерів API
app.include_router(utils.router, prefix="/api")
app.include_router(contacts.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    
    # Запуск FastAPI серверу
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)

