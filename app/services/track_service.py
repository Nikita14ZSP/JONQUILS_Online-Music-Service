from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func
from sqlalchemy.orm import selectinload
import requests
import os
import uuid
import aiofiles
from urllib.parse import urlparse
from pathlib import Path

from app.db.models import Track, Artist, Album, Genre
from app.schemas.track import TrackCreate, TrackUpdate, TrackSearchQuery, TrackWithDetails, TrackUploadFromURL, TrackUploadFromFile


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
    
    async def upload_track_from_url(self, track_data: TrackUploadFromURL) -> tuple[bool, str, Optional[Track]]:
        """Загрузка трека по URL"""
        try:
          
            existing_track_query = select(Track).where(Track.file_url == track_data.file_url)
            existing_result = await self.db.execute(existing_track_query)
            existing_track = existing_result.scalar_one_or_none()
            
            if existing_track:
                return False, "Трек с таким URL уже существует", existing_track
            
            
            try:
                response = requests.head(track_data.file_url, timeout=10)
                if response.status_code != 200:
                    return False, f"URL недоступен (статус: {response.status_code})", None
                
                
                content_type = response.headers.get('content-type', '').lower()
                if not any(audio_type in content_type for audio_type in ['audio/', 'application/ogg']):
                    return False, f"Файл по URL не является аудиофайлом (тип: {content_type})", None
                    
            except requests.RequestException as e:
                return False, f"Ошибка при проверке URL: {str(e)}", None
            
            
            artist_query = select(Artist).where(Artist.id == track_data.artist_id)
            artist_result = await self.db.execute(artist_query)
            artist = artist_result.scalar_one_or_none()
            
            if not artist:
                return False, f"Исполнитель с ID {track_data.artist_id} не найден", None
            
            if track_data.album_id:
                album_query = select(Album).where(Album.id == track_data.album_id)
                album_result = await self.db.execute(album_query)
                album = album_result.scalar_one_or_none()
                
                if not album:
                    return False, f"Альбом с ID {track_data.album_id} не найден", None
            
            if track_data.genre_id:
                genre_query = select(Genre).where(Genre.id == track_data.genre_id)
                genre_result = await self.db.execute(genre_query)
                genre = genre_result.scalar_one_or_none()
                
                if not genre:
                    return False, f"Жанр с ID {track_data.genre_id} не найден", None
            
            
            db_track = Track(
                title=track_data.title,
                artist_id=track_data.artist_id,
                album_id=track_data.album_id,
                genre_id=track_data.genre_id,
                file_url=track_data.file_url,
                explicit=track_data.explicit,
                preview_url=track_data.preview_url,
                popularity=0  
            )
            
            self.db.add(db_track)
            await self.db.commit()
            await self.db.refresh(db_track)
            
            return True, "Трек успешно загружен", db_track
            
        except Exception as e:
            await self.db.rollback()
            return False, f"Ошибка при загрузке трека: {str(e)}", None
    
  
    
    async def get_track_by_id(self, track_id: int) -> Optional[Track]:
        """Получение трека по ID (алиас для get_track)"""
        return await self.get_track(track_id)
    
    async def upload_track_from_file(self, track_data: TrackUploadFromFile, file_content: bytes, filename: str) -> tuple[bool, str, Optional[Track]]:
        """Загрузка трека из локального файла"""
        try:
            
            artist_query = select(Artist).where(Artist.id == track_data.artist_id)
            artist_result = await self.db.execute(artist_query)
            artist = artist_result.scalar_one_or_none()
            
            if not artist:
                return False, f"Исполнитель с ID {track_data.artist_id} не найден", None
            
            if track_data.album_id:
                album_query = select(Album).where(Album.id == track_data.album_id)
                album_result = await self.db.execute(album_query)
                album = album_result.scalar_one_or_none()
                
                if not album:
                    return False, f"Альбом с ID {track_data.album_id} не найден", None
            
            if track_data.genre_id:
                genre_query = select(Genre).where(Genre.id == track_data.genre_id)
                genre_result = await self.db.execute(genre_query)
                genre = genre_result.scalar_one_or_none()
                
                if not genre:
                    return False, f"Жанр с ID {track_data.genre_id} не найден", None
            
           
            allowed_extensions = ['.mp3', '.wav', '.flac', '.m4a', '.ogg', '.aac']
            file_extension = Path(filename).suffix.lower()
            
            if file_extension not in allowed_extensions:
                return False, f"Неподдерживаемый формат файла: {file_extension}. Поддерживаются: {', '.join(allowed_extensions)}", None
            
            
            upload_dir = Path("uploads/tracks")
            upload_dir.mkdir(parents=True, exist_ok=True)
            
            
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = upload_dir / unique_filename
            
           
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            
            
            db_track = Track(
                title=track_data.title,
                artist_id=track_data.artist_id,
                album_id=track_data.album_id,
                genre_id=track_data.genre_id,
                file_path=str(file_path),
                explicit=track_data.explicit,
                duration_ms=track_data.duration_ms,
                popularity=0  
            )
            
            self.db.add(db_track)
            await self.db.commit()
            await self.db.refresh(db_track)
            
            return True, "Трек успешно загружен", db_track
            
        except Exception as e:
            await self.db.rollback()
            
            if 'file_path' in locals() and file_path.exists():
                file_path.unlink()
            return False, f"Ошибка при загрузке трека: {str(e)}", None
