from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class AlbumBase(BaseModel):
    title: str = Field(..., description="Название альбома")
    cover_image_url: Optional[str] = Field(None, description="URL обложки альбома")

class AlbumCreate(AlbumBase):
    artist_id: int = Field(..., description="ID исполнителя")
    release_date: Optional[datetime] = Field(None, description="Дата выпуска")
    spotify_id: Optional[str] = Field(None, description="Spotify ID")

class AlbumUpdate(BaseModel):
    title: Optional[str] = None
    artist_id: Optional[int] = None
    release_date: Optional[datetime] = None
    cover_image_url: Optional[str] = None

class AlbumInDBBase(AlbumBase):
    id: int
    artist_id: int
    release_date: Optional[datetime]
    spotify_id: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class Album(AlbumInDBBase):
    pass

class AlbumWithDetails(AlbumInDBBase):
    """Альбом с подробной информацией"""
    artist_name: Optional[str] = None
    track_count: int = 0
    total_duration_ms: int = 0 