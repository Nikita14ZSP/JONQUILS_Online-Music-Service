from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class GenreBase(BaseModel):
    name: str = Field(..., description="Название жанра")
    description: Optional[str] = Field(None, description="Описание жанра")


class GenreCreate(GenreBase):
    pass


class GenreUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class GenreInDBBase(GenreBase):
    id: int
    
    class Config:
        from_attributes = True


class Genre(GenreInDBBase):
    pass


class GenreWithStats(GenreInDBBase):
    """Жанр со статистикой"""
    track_count: int = 0
    total_plays: int = 0
