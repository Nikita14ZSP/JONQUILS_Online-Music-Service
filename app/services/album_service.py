from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload

from app.db.models import Album, Track, Artist
from app.schemas.album import AlbumCreate, AlbumUpdate


class AlbumService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_albums(self, skip: int = 0, limit: int = 100) -> List[Album]:
        """Получить список альбомов с пагинацией."""
        query = select(Album).options(selectinload(Album.artist)).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_album_by_id(self, album_id: int) -> Optional[Album]:
        """Получить альбом по ID."""
        query = select(Album).options(selectinload(Album.artist)).where(Album.id == album_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_album_by_title_and_artist(self, title: str, artist_id: int) -> Optional[Album]:
        """Получить альбом по названию и исполнителю."""
        query = select(Album).where(
            Album.title == title,
            Album.artist_id == artist_id
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_album(self, album_data: AlbumCreate) -> Album:
        """Создать новый альбом."""
        db_album = Album(
            title=album_data.title,
            artist_id=album_data.artist_id,
            release_date=album_data.release_date,
            genre=album_data.genre,
            cover_url=album_data.cover_url,
            description=album_data.description
        )
        
        self.db.add(db_album)
        await self.db.commit()
        await self.db.refresh(db_album)
        return db_album

    async def update_album(self, album_id: int, album_data: AlbumUpdate) -> Optional[Album]:
        """Обновить альбом."""
        query = select(Album).where(Album.id == album_id)
        result = await self.db.execute(query)
        db_album = result.scalar_one_or_none()
        
        if not db_album:
            return None
        
        update_data = album_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_album, field, value)
        
        await self.db.commit()
        await self.db.refresh(db_album)
        return db_album

    async def delete_album(self, album_id: int) -> bool:
        """Удалить альбом."""
        query = select(Album).where(Album.id == album_id)
        result = await self.db.execute(query)
        db_album = result.scalar_one_or_none()
        
        if not db_album:
            return False
        
        await self.db.delete(db_album)
        await self.db.commit()
        return True

    async def search_albums(self, query: str, limit: int = 10) -> List[Album]:
        """Поиск альбомов по названию."""
        search_query = (
            select(Album)
            .options(selectinload(Album.artist))
            .where(Album.title.ilike(f"%{query}%"))
            .limit(limit)
        )
        
        result = await self.db.execute(search_query)
        return result.scalars().all()

    async def get_album_tracks(self, album_id: int) -> List[Track]:
        """Получить треки альбома."""
        query = select(Track).where(Track.album_id == album_id).order_by(Track.track_number)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_albums_by_artist(self, artist_id: int) -> List[Album]:
        """Получить альбомы исполнителя."""
        query = (
            select(Album)
            .options(selectinload(Album.artist))
            .where(Album.artist_id == artist_id)
            .order_by(desc(Album.release_date))
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_popular_albums(self, limit: int = 20) -> List[Album]:
        """Получить популярные альбомы на основе количества треков и прослушиваний."""
        # Простая реализация - по количеству треков
        # В реальном приложении это будет основано на аналитике прослушиваний
        query = (
            select(Album)
            .options(selectinload(Album.artist))
            .join(Track)
            .group_by(Album.id)
            .order_by(func.count(Track.id).desc())
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_recent_albums(self, limit: int = 20) -> List[Album]:
        """Получить недавно выпущенные альбомы."""
        query = (
            select(Album)
            .options(selectinload(Album.artist))
            .order_by(desc(Album.release_date))
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_albums_by_genre(self, genre: str, limit: int = 20) -> List[Album]:
        """Получить альбомы по жанру."""
        query = (
            select(Album)
            .options(selectinload(Album.artist))
            .where(Album.genre == genre)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_albums_by_year(self, year: int, limit: int = 20) -> List[Album]:
        """Получить альбомы по году выпуска."""
        query = (
            select(Album)
            .options(selectinload(Album.artist))
            .where(func.extract('year', Album.release_date) == year)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_album_stats(self, album_id: int) -> dict:
        """Получить статистику альбома."""
        # Количество треков
        tracks_query = select(func.count(Track.id)).where(Track.album_id == album_id)
        tracks_result = await self.db.execute(tracks_query)
        tracks_count = tracks_result.scalar()

        # Общая длительность альбома
        duration_query = select(func.sum(Track.duration_ms)).where(Track.album_id == album_id)
        duration_result = await self.db.execute(duration_query)
        total_duration = duration_result.scalar() or 0

        return {
            "album_id": album_id,
            "total_tracks": tracks_count,
            "total_duration_ms": total_duration,
            "average_track_duration_ms": total_duration // tracks_count if tracks_count > 0 else 0
        }
