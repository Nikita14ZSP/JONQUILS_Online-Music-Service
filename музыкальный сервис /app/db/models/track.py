from typing import Optional
from sqlmodel import Field, SQLModel # Пример, если будем использовать SQLModel

# Для начала, пока нет БД, можно использовать Pydantic модели и тут, 
# но в будущем это будут модели ORM (SQLAlchemy, SQLModel)

class TrackBase(SQLModel):
    title: str
    artist_id: Optional[int] = None # Связь с исполнителем
    album_id: Optional[int] = None  # Связь с альбомом
    genre: Optional[str] = None
    duration_ms: Optional[int] = None
    release_year: Optional[int] = None
    # file_path: str # Путь к файлу или ссылка на поток

class Track(TrackBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

# Если не используем SQLModel сразу, можно просто Pydantic:
# from pydantic import BaseModel
# class Track(BaseModel):
# id: int
# title: str
# artist: str # Для простоты пока строка, потом будет ссылка на модель Artist
# album: Optional[str] = None
# genre: Optional[str] = None
# duration_ms: int
# release_year: Optional[int] = None 