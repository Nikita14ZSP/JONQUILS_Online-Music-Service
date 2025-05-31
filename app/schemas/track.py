from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class TrackBase(BaseModel):
    title: str = Field(..., description="Название трека")
    duration_ms: Optional[int] = Field(None, description="Длительность в миллисекундах")
    explicit: bool = Field(False, description="Содержит ли трек нецензурный контент")
    popularity: int = Field(0, ge=0, le=100, description="Популярность трека 0-100")
    preview_url: Optional[str] = Field(None, description="URL превью трека")
    file_url: Optional[str] = Field(None, description="URL для стриминга")
    
    # Аудио характеристики
    tempo: Optional[float] = Field(None, description="Темп в BPM")
    energy: Optional[float] = Field(None, ge=0.0, le=1.0, description="Энергетика 0.0-1.0")
    valence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Позитивность 0.0-1.0")
    danceability: Optional[float] = Field(None, ge=0.0, le=1.0, description="Танцевальность 0.0-1.0")

class TrackCreate(TrackBase):
    artist_id: int = Field(..., description="ID исполнителя")
    album_id: Optional[int] = Field(None, description="ID альбома")
    genre_id: Optional[int] = Field(None, description="ID жанра")
    spotify_id: Optional[str] = Field(None, description="Spotify ID")

class TrackUpdate(BaseModel):
    title: Optional[str] = None
    artist_id: Optional[int] = None
    album_id: Optional[int] = None
    genre_id: Optional[int] = None
    duration_ms: Optional[int] = None
    explicit: Optional[bool] = None
    popularity: Optional[int] = Field(None, ge=0, le=100)
    preview_url: Optional[str] = None
    file_url: Optional[str] = None
    tempo: Optional[float] = None
    energy: Optional[float] = Field(None, ge=0.0, le=1.0)
    valence: Optional[float] = Field(None, ge=0.0, le=1.0)
    danceability: Optional[float] = Field(None, ge=0.0, le=1.0)

class TrackInDBBase(TrackBase):
    id: int
    artist_id: int
    album_id: Optional[int]
    genre_id: Optional[int]
    spotify_id: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class Track(TrackInDBBase):
    pass

class TrackWithDetails(TrackInDBBase):
    """Трек с подробной информацией об исполнителе, альбоме и жанре"""
    artist_name: Optional[str] = None
    album_title: Optional[str] = None
    genre_name: Optional[str] = None
    artist_image_url: Optional[str] = None
    album_cover_url: Optional[str] = None

# Схемы для поиска
class TrackSearchQuery(BaseModel):
    query: str = Field(..., description="Поисковый запрос")
    artist: Optional[str] = Field(None, description="Фильтр по исполнителю")
    album: Optional[str] = Field(None, description="Фильтр по альбому")
    genre: Optional[str] = Field(None, description="Фильтр по жанру")
    year_from: Optional[int] = Field(None, description="Год выпуска от")
    year_to: Optional[int] = Field(None, description="Год выпуска до")
    duration_from: Optional[int] = Field(None, description="Минимальная длительность в мс")
    duration_to: Optional[int] = Field(None, description="Максимальная длительность в мс")
    limit: int = Field(20, ge=1, le=100, description="Количество результатов")
    offset: int = Field(0, ge=0, description="Смещение для пагинации")

class TrackSearchResponse(BaseModel):
    tracks: list[TrackWithDetails]
    total: int
    limit: int
    offset: int 