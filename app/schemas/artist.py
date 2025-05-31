from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ArtistBase(BaseModel):
    name: str = Field(..., description="Имя исполнителя")
    bio: Optional[str] = Field(None, description="Биография исполнителя")
    country: Optional[str] = Field(None, description="Страна")
    image_url: Optional[str] = Field(None, description="URL изображения")

class ArtistCreate(ArtistBase):
    spotify_id: Optional[str] = Field(None, description="Spotify ID")

class ArtistUpdate(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    country: Optional[str] = None
    image_url: Optional[str] = None

class ArtistInDBBase(ArtistBase):
    id: int
    spotify_id: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

class Artist(ArtistInDBBase):
    pass

class ArtistWithStats(ArtistInDBBase):
    """Исполнитель со статистикой"""
    total_tracks: int = 0
    total_albums: int = 0
    total_plays: int = 0
    monthly_listeners: int = 0 