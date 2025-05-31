from pydantic import BaseModel
from typing import Optional

class ArtistBase(BaseModel):
    name: str

class ArtistCreate(ArtistBase):
    pass

class ArtistUpdate(ArtistBase):
    name: Optional[str] = None

class Artist(ArtistBase):
    id: int

    class Config:
        orm_mode = True 