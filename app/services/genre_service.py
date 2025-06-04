from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from typing import List, Optional

from app.db.models import Genre, Track
from app.schemas.genre import GenreCreate, GenreUpdate, GenreWithStats


class GenreService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, genre_data: GenreCreate) -> Genre:
        """Создать новый жанр"""
        db_genre = Genre(
            name=genre_data.name,
            description=genre_data.description
        )
        self.db.add(db_genre)
        await self.db.commit()
        await self.db.refresh(db_genre)
        return db_genre

    async def get_by_id(self, genre_id: int) -> Optional[Genre]:
        """Получить жанр по ID"""
        result = await self.db.execute(select(Genre).filter(Genre.id == genre_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> Optional[Genre]:
        """Получить жанр по имени"""
        result = await self.db.execute(select(Genre).filter(Genre.name == name))
        return result.scalar_one_or_none()

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Genre]:
        """Получить все жанры"""
        result = await self.db.execute(select(Genre).offset(skip).limit(limit))
        return result.scalars().all()

    async def update(self, genre_id: int, genre_data: GenreUpdate) -> Genre:
        """Обновить жанр"""
        result = await self.db.execute(select(Genre).filter(Genre.id == genre_id))
        db_genre = result.scalar_one_or_none()
        if not db_genre:
            return None

        update_data = genre_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_genre, field, value)

        await self.db.commit()
        await self.db.refresh(db_genre)
        return db_genre

    async def delete(self, genre_id: int) -> bool:
        """Удалить жанр"""
        result = await self.db.execute(select(Genre).filter(Genre.id == genre_id))
        db_genre = result.scalar_one_or_none()
        if not db_genre:
            return False

        await self.db.delete(db_genre)
        await self.db.commit()
        return True

    async def get_with_stats(self, genre_id: int) -> Optional[GenreWithStats]:
        """Получить жанр со статистикой"""
        result = await self.db.execute(select(Genre).filter(Genre.id == genre_id))
        genre = result.scalar_one_or_none()
        if not genre:
            return None

        track_count_result = await self.db.execute(
            select(func.count(Track.id)).filter(Track.genre_id == genre_id)
        )
        track_count = track_count_result.scalar() or 0

        return GenreWithStats(
            id=genre.id,
            name=genre.name,
            description=genre.description,
            track_count=track_count,
            total_plays=0  
        )
