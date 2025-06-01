from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from app.api.v1 import api_router as api_router_v1
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Онлайн музыкальный сервис с аналитикой и рекомендациями",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Настройка CORS для фронтенда
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router_v1, prefix=settings.API_V1_STR)

@app.get("/", summary="Главная страница API")
def root():
    """
    Главная страница API музыкального сервиса.
    """
    return {
        "message": "JONQUILS Online Music Service API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }

@app.get("/health", summary="Проверка состояния API")
def health_check():
    """
    Проверка работоспособности API.
    """
    return {"status": "healthy", "service": "music-api"}

@app.get("/ping", summary="Check if the API is alive")
def pong():
    """
    Sanity check for the API.
    """
    return {"ping": "pong!"}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)