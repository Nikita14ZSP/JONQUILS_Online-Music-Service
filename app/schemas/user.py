from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, description="Имя пользователя")
    email: EmailStr = Field(..., description="Email пользователя")
    full_name: Optional[str] = Field(None, max_length=255, description="Полное имя пользователя")
    role: str = "listener" 

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Пароль пользователя")

class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None
    is_premium: Optional[bool] = None

class UserInDBBase(UserBase):
    id: int
    is_active: bool
    is_premium: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class User(UserInDBBase):
    artist_profile_id: Optional[int] = None 

    class Config:
        from_attributes = True

class UserProfile(UserInDBBase):
    """Профиль пользователя с дополнительной информацией"""
    total_listening_time: int = 0  
    favorite_genres: list[str] = []
    total_playlists: int = 0


class UserLogin(BaseModel):
    username: str = Field(..., description="Имя пользователя или email")
    password: str = Field(..., description="Пароль")

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenData(BaseModel):
    username: Optional[str] = None
