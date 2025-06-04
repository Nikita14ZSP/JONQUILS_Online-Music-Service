from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.db.models import User, Artist

security = HTTPBearer(auto_error=False)

async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Получение текущего пользователя из токена.
    Упрощенная версия - в реальном проекте нужна JWT аутентификация.
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    

    try:
        result = await db.execute(select(User).limit(1))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

async def get_current_artist(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> Artist:
    """
    Получение текущего артиста на основе пользователя.
    """
    try:
        result = await db.execute(
            select(Artist).where(Artist.user_id == current_user.id)
        )
        artist = result.scalar_one_or_none()
        if not artist:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is not an artist"
            )
        return artist
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving artist profile"
        )

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Получение активного пользователя.
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user

async def get_current_premium_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Получение премиум пользователя.
    """
    if not current_user.is_premium:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium subscription required"
        )
    return current_user
