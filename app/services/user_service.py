from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from fastapi import HTTPException, status 

from app.db.models import User, Artist, UserPreference 
from app.schemas.user import UserCreate, UserUpdate

from app.schemas.auth import RegisterRequest as RegisterRequestSchema
from app.schemas.artist import ArtistCreate 


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_users(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Получить список пользователей с пагинацией."""
        query = select(User).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID."""
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Получить пользователя по email."""
        query = select(User).where(User.email == email)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Получить пользователя по username."""
        query = select(User).where(User.username == username)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def create_user(self, user_data: RegisterRequestSchema) -> User:
        """Создать нового пользователя и, если это артист, его профиль."""
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        hashed_password = pwd_context.hash(user_data.password)
        
        db_user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            role=user_data.role, 
            is_active=True
        )
        
        self.db.add(db_user)
        await self.db.flush() 

        if user_data.role == "artist":
            if not user_data.artist_name:
                await self.db.rollback() 
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Artist name is required for artist role."
                )
            
            
            artist_create_data = {
                "name": user_data.artist_name
            }
            if user_data.bio is not None: 
                artist_create_data["bio"] = user_data.bio
            if user_data.country is not None:
                artist_create_data["country"] = user_data.country
            if user_data.image_url is not None:
                artist_create_data["image_url"] = user_data.image_url

            artist_profile_data = ArtistCreate(**artist_create_data)
            
            db_artist = Artist(
                **artist_profile_data.model_dump(exclude_unset=True), 
                user_id=db_user.id  
            )
            self.db.add(db_artist)
        
        await self.db.commit()
        await self.db.refresh(db_user)
        
        if db_user.role == "artist":
            await self.db.refresh(db_user, relationship_names=["artist_profile"])

        return db_user

    async def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """Обновить пользователя."""
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            return None
        
        update_data = user_data.dict(exclude_unset=True)
        
        
        if "password" in update_data:
            from passlib.context import CryptContext
            pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
            update_data["hashed_password"] = pwd_context.hash(update_data.pop("password"))
        
        for field, value in update_data.items():
            setattr(db_user, field, value)
        
        await self.db.commit()
        await self.db.refresh(db_user)
        return db_user

    async def delete_user(self, user_id: int) -> bool:
        """Удалить пользователя."""
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        db_user = result.scalar_one_or_none()
        
        if not db_user:
            return False
        
        await self.db.delete(db_user)
        await self.db.commit()
        return True

    async def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Аутентификация пользователя."""
        user = await self.get_user_by_username(username)
        if not user:
            user = await self.get_user_by_email(username)
        
        if not user:
            return None
        
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
        if not pwd_context.verify(password, user.hashed_password):
            return None
        
        return user

    async def get_user_playlists(self, user_id: int) -> List:
        """Получить плейлисты пользователя."""
        query = select(User).options(selectinload(User.playlists)).where(User.id == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return []
        
        return user.playlists

    async def get_user_preferences(self, user_id: int) -> Optional[List[UserPreference]]:
        """Получить предпочтения пользователя."""
        query = select(User).options(selectinload(User.preferences)).where(User.id == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return None
        
        return user.preferences

    async def get_user_with_artist_profile(self, user_id: int) -> Optional[User]:
        """Получить пользователя с загруженным профилем артиста."""
        query = select(User).options(selectinload(User.artist_profile)).where(User.id == user_id)
        result = await self.db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            return None
            
        
        if user.artist_profile:
            user.artist_profile_id = user.artist_profile.id
            
        return user
