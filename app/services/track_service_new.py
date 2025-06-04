from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload

from app.db.models import Track, Artist, Album, Genre
from app.schemas.track import TrackCreate, TrackUpdate, TrackSearchQuery, TrackWithDetails


class TrackService:
    """Сервис для работы с треками"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_track(self, track_data: TrackCreate) -> Track:
        """Создание нового трека"""
        db_track = Track(**track_data.model_dump())
        self.db.add(db_track)
        await self.db.commit()
        await self.db.refresh(db_track)
        return db_track
    
    async def get_track(self, track_id: int) -> Optional[Track]:
        """Получение трека по ID"""
        query = select(Track).where(Track.id == track_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
    
    async def get_track_with_details(self, track_id: int) -> Optional[TrackWithDetails]:
        """Получение трека с деталями об исполнителе, альбоме и жанре"""
        query = (
            select(
                Track,
                Artist.name.label("artist_name"),
                Artist.image_url.label("artist_image_url"),
                Album.title.label("album_title"),
                Album.cover_image_url.label("album_cover_url"),
                Genre.name.label("genre_name")
            )
            .outerjoin(Artist, Track.artist_id == Artist.id)
            .outerjoin(Album, Track.album_id == Album.id)
            .outerjoin(Genre, Track.genre_id == Genre.id)
            .where(Track.id == track_id)
        )
        
        result = await self.db.execute(query)
        row = result.first()
        
        if not row:
            return None
        
        track = row[0]
        return TrackWithDetails(
            **track.__dict__,
            artist_name=row.artist_name,
            artist_image_url=row.artist_image_url,
            album_title=row.album_title,
            album_cover_url=row.album_cover_url,
            genre_name=row.genre_name
        )
    
    async def get_tracks(self, skip: int = 0, limit: int = 100) -> List[Track]:
        """Получение списка треков с пагинацией"""
        query = select(Track).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def update_track(self, track_id: int, track_data: TrackUpdate) -> Optional[Track]:
        """Обновление трека"""
        db_track = await self.get_track(track_id)
        if not db_track:
            return None
        
        update_data = track_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_track, field, value)
        
        await self.db.commit()
        await self.db.refresh(db_track)
        return db_track
    
    async def delete_track(self, track_id: int) -> bool:
        """Удаление трека"""
        db_track = await self.get_track(track_id)
        if not db_track:
            return False
        
        await self.db.delete(db_track)
        await self.db.commit()
        return True
    
    async def search_tracks(self, search_query: TrackSearchQuery) -> tuple[List[TrackWithDetails], int]:
        """Поиск треков с фильтрацией"""
       
        base_query = (
            select(
                Track,
                Artist.name.label("artist_name"),
                Artist.image_url.label("artist_image_url"),
                Album.title.label("album_title"),
                Album.cover_image_url.label("album_cover_url"),
                Genre.name.label("genre_name")
            )
            .outerjoin(Artist, Track.artist_id == Artist.id)
            .outerjoin(Album, Track.album_id == Album.id)
            .outerjoin(Genre, Track.genre_id == Genre.id)
        )
        
        
        conditions = []
        
        
        if search_query.query:
            conditions.append(
                or_(
                    Track.title.ilike(f"%{search_query.query}%"),
                    Artist.name.ilike(f"%{search_query.query}%"),
                    Album.title.ilike(f"%{search_query.query}%")
                )
            )
        
        
        if search_query.artist:
            conditions.append(Artist.name.ilike(f"%{search_query.artist}%"))
        
        if search_query.album:
            conditions.append(Album.title.ilike(f"%{search_query.album}%"))
        
        if search_query.genre:
            conditions.append(Genre.name.ilike(f"%{search_query.genre}%"))
        
        if search_query.duration_from:
            conditions.append(Track.duration_ms >= search_query.duration_from)
        
        if search_query.duration_to:
            conditions.append(Track.duration_ms <= search_query.duration_to)
        
        
        if conditions:
            base_query = base_query.where(and_(*conditions))
        
        
        count_query = select(func.count()).select_from(
            base_query.subquery()
        )
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        
        query = base_query.offset(search_query.offset).limit(search_query.limit)
        result = await self.db.execute(query)
        rows = result.all()
        
        
        tracks = []
        for row in rows:
            track = row[0]
            track_with_details = TrackWithDetails(
                **track.__dict__,
                artist_name=row.artist_name,
                artist_image_url=row.artist_image_url,
                album_title=row.album_title,
                album_cover_url=row.album_cover_url,
                genre_name=row.genre_name
            )
            tracks.append(track_with_details)
        
        return tracks, total
    
    async def get_tracks_by_artist(self, artist_id: int, skip: int = 0, limit: int = 100) -> List[Track]:
        """Получение треков по исполнителю"""
        query = (
            select(Track)
            .where(Track.artist_id == artist_id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_tracks_by_album(self, album_id: int) -> List[Track]:
        """Получение треков по альбому"""
        query = select(Track).where(Track.album_id == album_id)
        result = await self.db.execute(query)
        return result.scalars().all()
    
    async def get_popular_tracks(self, limit: int = 50) -> List[TrackWithDetails]:
        """Получение популярных треков"""
        query = (
            select(
                Track,
                Artist.name.label("artist_name"),
                Artist.image_url.label("artist_image_url"),
                Album.title.label("album_title"),
                Album.cover_image_url.label("album_cover_url"),
                Genre.name.label("genre_name")
            )
            .outerjoin(Artist, Track.artist_id == Artist.id)
            .outerjoin(Album, Track.album_id == Album.id)
            .outerjoin(Genre, Track.genre_id == Genre.id)
            .order_by(Track.popularity.desc())
            .limit(limit)
        )
        
        result = await self.db.execute(query)
        rows = result.all()
        
        tracks = []
        for row in rows:
            track = row[0]
            track_with_details = TrackWithDetails(
                **track.__dict__,
                artist_name=row.artist_name,
                artist_image_url=row.artist_image_url,
                album_title=row.album_title,
                album_cover_url=row.album_cover_url,
                genre_name=row.genre_name
            )
            tracks.append(track_with_details)
        
        return tracks
