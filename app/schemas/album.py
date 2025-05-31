from pydantic import BaseModel
from typing import Optional

class AlbumBase(BaseModel):
    title: str
    artist_id: Optional[int] = None
    release_year: Optional[int] = None

class AlbumCreate(AlbumBase):
    pass

class AlbumUpdate(AlbumBase):
    title: Optional[str] = None

class Album(AlbumBase):
    id: int
    artist_name: Optional[str] = None # Пример

    class Config:
        orm_mode = True 