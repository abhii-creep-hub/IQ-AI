from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.schemas.user import (
    UserCreate, UserUpdate, UserResponse, LoginRequest,
    TokenResponse, RefreshTokenRequest, PasswordChange,
    ForgotPasswordRequest, ResetPasswordRequest, MessageResponse,
)
from app.services.user_service import UserService
from app.middleware.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    try:
        user = await service.register(
            email=data.email,
            username=data.username,
            password=data.password,
            full_name=data.full_name,
            role=data.role,
        )
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    try:
        result = await service.login(email=data.email, password=data.password)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    try:
        result = await service.refresh_token(data.refresh_token)
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    token = await service.forgot_password(data.email)
    if token:
        return MessageResponse(message="Password reset email sent", success=True)
    return MessageResponse(message="If the email exists, a reset link has been sent", success=True)


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    try:
        await service.reset_password(data.token, data.new_password)
        return MessageResponse(message="Password reset successfully", success=True)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    try:
        await service.change_password(current_user.id, data.current_password, data.new_password)
        return MessageResponse(message="Password changed successfully", success=True)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_me(
    data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    service = UserService(db)
    try:
        user = await service.update_user(
            current_user.id,
            full_name=data.full_name,
            phone=data.phone,
            company=data.company,
            designation=data.designation,
            avatar_url=data.avatar_url,
        )
        return user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
