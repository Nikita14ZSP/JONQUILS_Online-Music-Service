from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.db.models import Artist, Track, Album
from app.schemas.artist import ArtistCreate, ArtistUpdate


class ArtistService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_artists(self, skip: int = 0, limit: int = 100) -> List[Artist]:
        """Получить список исполнителей с пагинацией."""
        query = select(Artist).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_artist_by_id(self, artist_id: int) -> Optional[Artist]:
        """Получить исполнителя по ID."""
        query = select(Artist).where(Artist.id == artist_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_artist_by_name(self, name: str) -> Optional[Artist]:
        """Получить исполнителя по имени."""
        query = select(Artist).where(Artist.name == name)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_artist(self, artist_data: ArtistCreate) -> Artist:
        """Создать нового исполнителя."""
        db_artist = Artist(
            name=artist_data.name,
            bio=artist_data.bio,
            country=artist_data.country,
            genre=artist_data.genre,
            image_url=artist_data.image_url
        )
        
        self.db.add(db_artist)
        await self.db.commit()
        await self.db.refresh(db_artist)
        return db_artist

    async def update_artist(self, artist_id: int, artist_data: ArtistUpdate) -> Optional[Artist]:
        """Обновить исполнителя."""
        query = select(Artist).where(Artist.id == artist_id)
        result = await self.db.execute(query)
        db_artist = result.scalar_one_or_none()
        
        if not db_artist:
            return None
        
        update_data = artist_data.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_artist, field, value)
        
        await self.db.commit()
        await self.db.refresh(db_artist)
        return db_artist

    async def delete_artist(self, artist_id: int) -> bool:
        """Удалить исполнителя."""
        query = select(Artist).where(Artist.id == artist_id)
        result = await self.db.execute(query)
        db_artist = result.scalar_one_or_none()
        
        if not db_artist:
            return False
        
        await self.db.delete(db_artist)
        await self.db.commit()
        return True

    async def search_artists(self, query: str, limit: int = 10) -> List[Artist]:
        """Поиск исполнителей по имени."""
        search_query = select(Artist).where(
            Artist.name.ilike(f"%{query}%")
        ).limit(limit)
        
        result = await self.db.execute(search_query)
        return result.scalars().all()

    async def get_artist_tracks(self, artist_id: int, limit: int = 20) -> List[Track]:
        """Получить треки исполнителя."""
        query = select(Track).where(Track.artist_id == artist_id).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_artist_albums(self, artist_id: int) -> List[Album]:
        """Получить альбомы исполнителя."""
        query = select(Album).where(Album.artist_id == artist_id)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_popular_artists(self, limit: int = 20) -> List[Artist]:
        """Получить популярных исполнителей на основе количества прослушиваний их треков."""
        # Сначала простая реализация - по количеству треков
        # В реальном приложении это будет основано на аналитике прослушиваний
        query = (
            select(Artist)
            .join(Track)
            .group_by(Artist.id)
            .order_by(func.count(Track.id).desc())
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_artists_by_genre(self, genre: str, limit: int = 20) -> List[Artist]:
        """Получить исполнителей по жанру."""
        query = select(Artist).where(Artist.genre == genre).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_artists_by_country(self, country: str, limit: int = 20) -> List[Artist]:
        """Получить исполнителей по стране."""
        query = select(Artist).where(Artist.country == country).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_artist_stats(self, artist_id: int) -> dict:
        """Получить статистику исполнителя."""
        # Количество треков
        tracks_query = select(func.count(Track.id)).where(Track.artist_id == artist_id)
        tracks_result = await self.db.execute(tracks_query)
        tracks_count = tracks_result.scalar()

        # Количество альбомов
        albums_query = select(func.count(Album.id)).where(Album.artist_id == artist_id)
        albums_result = await self.db.execute(albums_query)
        albums_count = albums_result.scalar()

        return {
            "artist_id": artist_id,
            "total_tracks": tracks_count,
            "total_albums": albums_count
        }
