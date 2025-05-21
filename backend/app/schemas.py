from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    class Config:
        orm_mode = True

class SongBase(BaseModel):
    title: str
    artist: str
    genre: str
    release_year: int

class SongCreate(SongBase):
    pass

class Song(SongBase):
    id: int
    class Config:
        orm_mode = True

class UserActionCreate(BaseModel):
    user_id: int
    song_id: int
    action_type: str

class UserAction(BaseModel):
    id: int
    user_id: int
    song_id: int
    action_type: str
    timestamp: datetime
    class Config:
        orm_mode = True

