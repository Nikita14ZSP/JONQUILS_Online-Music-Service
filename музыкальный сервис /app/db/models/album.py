from typing import Optional
from sqlmodel import Field, SQLModel

class AlbumBase(SQLModel):
    title: str
    artist_id: Optional[int] = Field(default=None, foreign_key="artist.id")
    release_year: Optional[int] = None

class Album(AlbumBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True) 