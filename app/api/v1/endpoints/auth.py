from datetime import timedelta
from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.auth import Token, LoginRequest, RegisterRequest, LoginResponse
from app.schemas.user import User
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.core.config import settings
from app.db.database import get_db
from app.core.security import get_current_active_user

router = APIRouter()

async def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    return AuthService(db)

async def get_user_service(db: AsyncSession = Depends(get_db)) -> UserService:
    return UserService(db)

@router.post("/login", response_model=LoginResponse, summary="Вход в систему")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service)
):
    """
    Аутентификация пользователя и получение JWT токена.
    """
    user = await auth_service.authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    full_user_info = await user_service.get_user_with_artist_profile(user.id)
    if not full_user_info:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found after authentication")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": access_token_expires.total_seconds(),
        "user": full_user_info
    }

@router.post("/login-json", response_model=LoginResponse, summary="Вход в систему (JSON)")
async def login_json(
    login_data: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
    user_service: UserService = Depends(get_user_service)
):
    """
    Аутентификация пользователя через JSON и получение JWT токена.
    """
    user = await auth_service.authenticate_user(login_data.username, login_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    full_user_info = await user_service.get_user_with_artist_profile(user.id)
    if not full_user_info:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found after authentication")

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": access_token_expires.total_seconds(),
        "user": full_user_info
    }

@router.post("/register", response_model=User, status_code=201, summary="Регистрация пользователя")
async def register(
    register_data: RegisterRequest,
    user_service: UserService = Depends(get_user_service)
):
    """
    Регистрация нового пользователя.
    """
    existing_user_email = await user_service.get_user_by_email(email=register_data.email)
    if existing_user_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    existing_user_username = await user_service.get_user_by_username(username=register_data.username)
    if existing_user_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this username already exists"
        )
    
    return await user_service.create_user(user_data=register_data)

@router.post("/refresh", response_model=Token, summary="Обновление токена")
async def refresh_token(
    current_user: User = Depends(get_auth_service),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Обновление JWT токена.
    """
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth_service.create_access_token(
        data={"sub": current_user.username}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/me", response_model=User, summary="Получить информацию о текущем пользователе")
async def read_users_me(
    current_user: User = Depends(get_current_active_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Получить информацию о текущем аутентифицированном пользователе.
    """
    user_with_profile = await user_service.get_user_with_artist_profile(current_user.id)
    return user_with_profile if user_with_profile else current_user
