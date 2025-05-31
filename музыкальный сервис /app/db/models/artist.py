from typing import Optional
from sqlmodel import Field, SQLModel

class ArtistBase(SQLModel):
    name: str

class Artist(ArtistBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True) 