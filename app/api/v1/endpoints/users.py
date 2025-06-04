from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Body, Path, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.user import User, UserCreate, UserUpdate
from app.services.user_service import UserService
from app.services.analytics_service import AnalyticsService
from app.db.database import get_db

router = APIRouter()

async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)

async def get_analytics_service(db: AsyncSession = Depends(get_db)) -> AnalyticsService:
    return AnalyticsService(db)

@router.get("/", response_model=List[User], summary="Получить список пользователей")
async def read_users(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
    user_service: UserService = Depends(get_user_service)
):
    """
    Получить список пользователей с пагинацией.
    """
    users = await user_service.get_users(skip=skip, limit=limit)
    return users

@router.post("/", response_model=User, status_code=201, summary="Создать нового пользователя")
async def create_user(
    user_in: UserCreate = Body(...),
    user_service: UserService = Depends(get_user_service)
):
    """
    Создать нового пользователя.
    """
    existing_user = await user_service.get_user_by_email(email=user_in.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    return await user_service.create_user(user_data=user_in)

@router.get("/{user_id}", response_model=User, summary="Получить пользователя по ID")
async def read_user(
    user_id: int = Path(..., title="ID пользователя", ge=1),
    user_service: UserService = Depends(get_user_service)
):
    """
    Получить информацию о конкретном пользователе по его ID.
    """
    db_user = await user_service.get_user_by_id(user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.put("/{user_id}", response_model=User, summary="Обновить пользователя")
async def update_user(
    user_id: int = Path(..., title="ID пользователя", ge=1),
    user_update: UserUpdate = Body(...),
    user_service: UserService = Depends(get_user_service)
):
    """
    Обновить информацию о пользователе.
    """
    updated_user = await user_service.update_user(user_id=user_id, user_data=user_update)
    if updated_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user

@router.delete("/{user_id}", status_code=204, summary="Удалить пользователя")
async def delete_user(
    user_id: int = Path(..., title="ID пользователя", ge=1),
    user_service: UserService = Depends(get_user_service)
):
    """
    Удалить пользователя.
    """
    deleted = await user_service.delete_user(user_id=user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")

@router.get("/{user_id}/listening-history", summary="Получить историю прослушиваний пользователя")
async def get_user_listening_history(
    user_id: int = Path(..., title="ID пользователя", ge=1),
    limit: int = Query(default=50, ge=1, le=100),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Получить историю прослушиваний пользователя.
    """
    history = await analytics_service.get_user_listening_history(user_id=user_id, limit=limit)
    return {"user_id": user_id, "listening_history": history}

@router.get("/{user_id}/stats", summary="Получить статистику пользователя")
async def get_user_stats(
    user_id: int = Path(..., title="ID пользователя", ge=1),
    period: str = Query(default="week", regex="^(week|month|year)$"),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Получить статистику прослушиваний пользователя за период.
    """
    stats = await analytics_service.get_user_stats(user_id=user_id, period=period)
    return stats
