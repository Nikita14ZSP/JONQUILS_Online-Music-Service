from typing import Optional
from pydantic import BaseModel

class TrackBase(BaseModel):
    title: str
    artist_name: Optional[str] = None # В схемах можем показывать имя, а не ID
    album_name: Optional[str] = None  # Аналогично
    genre: Optional[str] = None
    duration_ms: Optional[int] = None
    release_year: Optional[int] = None

class TrackCreate(TrackBase):
    pass

class TrackUpdate(TrackBase):
    title: Optional[str] = None # Все поля опциональны для обновления

class TrackInDBBase(TrackBase):
    id: int

    class Config:
        orm_mode = True # Для FastAPI, чтобы Pydantic мог работать с ORM моделями

class Track(TrackInDBBase):
    pass

class TrackSearchResults(BaseModel):
    results: list[Track] 