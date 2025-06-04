from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional

from app.db.database import get_db
from app.schemas.genre import Genre, GenreCreate, GenreUpdate, GenreWithStats
from app.services.genre_service import GenreService

router = APIRouter()


@router.post("/", response_model=Genre, status_code=status.HTTP_201_CREATED)
async def create_genre(
    genre_data: GenreCreate,
    db: AsyncSession = Depends(get_db)
):
    """Создать новый жанр"""
    genre_service = GenreService(db)
    
    # Проверяем, что жанр с таким именем не существует
    existing_genre = await genre_service.get_by_name(genre_data.name)
    if existing_genre:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Жанр с именем '{genre_data.name}' уже существует"
        )
    
    return await genre_service.create(genre_data)


@router.get("/", response_model=List[Genre])
async def get_genres(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """Получить список жанров"""
    genre_service = GenreService(db)
    return await genre_service.get_all(skip=skip, limit=limit)


@router.get("/{genre_id}", response_model=Genre)
async def get_genre(
    genre_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить жанр по ID"""
    genre_service = GenreService(db)
    genre = await genre_service.get_by_id(genre_id)
    if not genre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Жанр не найден"
        )
    return genre


@router.get("/name/{genre_name}", response_model=Genre)
async def get_genre_by_name(
    genre_name: str,
    db: AsyncSession = Depends(get_db)
):
    """Получить жанр по имени"""
    genre_service = GenreService(db)
    genre = await genre_service.get_by_name(genre_name)
    if not genre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Жанр '{genre_name}' не найден"
        )
    return genre


@router.put("/{genre_id}", response_model=Genre)
async def update_genre(
    genre_id: int,
    genre_data: GenreUpdate,
    db: AsyncSession = Depends(get_db)
):
    """Обновить жанр"""
    genre_service = GenreService(db)
    genre = await genre_service.get_by_id(genre_id)
    if not genre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Жанр не найден"
        )
    
    return await genre_service.update(genre_id, genre_data)


@router.delete("/{genre_id}")
async def delete_genre(
    genre_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Удалить жанр"""
    genre_service = GenreService(db)
    genre = await genre_service.get_by_id(genre_id)
    if not genre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Жанр не найден"
        )
    
    await genre_service.delete(genre_id)
    return {"detail": "Жанр успешно удален"}


@router.get("/{genre_id}/stats", response_model=GenreWithStats)
async def get_genre_stats(
    genre_id: int,
    db: AsyncSession = Depends(get_db)
):
    """Получить статистику жанра"""
    genre_service = GenreService(db)
    genre = await genre_service.get_by_id(genre_id)
    if not genre:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Жанр не найден"
        )
    
    return await genre_service.get_with_stats(genre_id)
