from typing import Optional
from pydantic import BaseModel
from app.schemas.user import User


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str
    full_name: Optional[str] = None
    role: str = "listener"  # Добавлено поле role
    # Поля для артиста, если role == "artist"
    artist_name: Optional[str] = None
    bio: Optional[str] = None
    country: Optional[str] = None
    image_url: Optional[str] = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: User
