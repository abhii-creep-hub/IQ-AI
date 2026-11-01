import logging
import hashlib
import smtplib
from email.message import EmailMessage
from typing import Optional
from uuid import UUID
from urllib.parse import quote
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.config import settings

logger = logging.getLogger(__name__)


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = UserRepository(db)

    async def register(self, email: str, username: str, password: str, full_name: Optional[str] = None) -> User:
        existing = await self.repo.get_by_email(email)
        if existing:
            raise ValueError("Email already registered")
        existing_user = await self.repo.get_by_username(username)
        if existing_user:
            raise ValueError("Username already taken")
        user = User(
            email=email,
            username=username,
            full_name=full_name,
            hashed_password=get_password_hash(password),
            # Public registration must never grant privileged roles.
            role="recruiter",
        )
        return await self.repo.create(user)

    async def login(self, email: str, password: str) -> dict:
        user = await self.repo.get_by_email(email)
        if not user:
            raise ValueError("Invalid email or password")
        if not verify_password(password, user.hashed_password):
            raise ValueError("Invalid email or password")
        if not user.is_active:
            raise ValueError("Account is deactivated")
        access_token = create_access_token(user.id)
        refresh_token = create_refresh_token(user.id)
        from datetime import datetime, timezone
        user.last_login = datetime.now(timezone.utc)
        await self.repo.update(user)
        from app.schemas.user import UserResponse
        user_data = UserResponse.model_validate(user)
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "user": user_data,
        }

    async def refresh_token(self, refresh_token: str) -> dict:
        payload = decode_token(refresh_token)
        if not payload or payload.get("type") != "refresh":
            raise ValueError("Invalid refresh token")
        user_id = payload.get("sub")
        user = await self.repo.get_by_id(UUID(user_id))
        if not user or not user.is_active:
            raise ValueError("User not found or inactive")
        access_token = create_access_token(user.id)
        new_refresh_token = create_refresh_token(user.id)
        from app.schemas.user import UserResponse
        user_data = UserResponse.model_validate(user)
        return {
            "access_token": access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "user": user_data,
        }

    async def get_user(self, user_id: UUID) -> Optional[User]:
        return await self.repo.get_by_id(user_id)

    async def update_user(self, user_id: UUID, **kwargs) -> User:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        for key, value in kwargs.items():
            if value is not None and hasattr(user, key):
                setattr(user, key, value)
        return await self.repo.update(user)

    async def change_password(self, user_id: UUID, current_password: str, new_password: str) -> bool:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise ValueError("User not found")
        if not verify_password(current_password, user.hashed_password):
            raise ValueError("Current password is incorrect")
        user.hashed_password = get_password_hash(new_password)
        await self.repo.update(user)
        return True

    async def forgot_password(self, email: str) -> Optional[str]:
        user = await self.repo.get_by_email(email)
        if not user:
            return None
        import secrets
        token = secrets.token_urlsafe(32)
        from datetime import datetime, timedelta, timezone
        user.reset_token = hashlib.sha256(token.encode()).hexdigest()
        user.reset_token_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        await self.repo.update(user)
        return token

    @staticmethod
    def send_password_reset_email(email: str, token: str) -> None:
        if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
            logger.error("Password reset email not sent: SMTP_USER and SMTP_PASSWORD are not configured")
            return

        reset_url = f"{settings.FRONTEND_URL.rstrip('/')}/reset-password?token={quote(token)}"
        message = EmailMessage()
        message["Subject"] = "Reset your IQ-AI password"
        message["From"] = settings.SMTP_FROM
        message["To"] = email
        message.set_content(
            "We received a request to reset your IQ-AI password. "
            f"Use this link within one hour: {reset_url}\n\n"
            "If you did not request this, you can ignore this email."
        )
        try:
            with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=15) as server:
                server.starttls()
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                server.send_message(message)
        except (OSError, smtplib.SMTPException):
            logger.exception("Password reset email delivery failed")

    async def reset_password(self, token: str, new_password: str) -> bool:
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        user = await self.repo.get_by_reset_token(token_hash)
        if not user:
            raise ValueError("Invalid or expired reset token")
        from datetime import datetime, timezone
        expires_at = user.reset_token_expires
        if expires_at and expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if not expires_at or expires_at < datetime.now(timezone.utc):
            raise ValueError("Reset token has expired")
        user.hashed_password = get_password_hash(new_password)
        user.reset_token = None
        user.reset_token_expires = None
        await self.repo.update(user)
        return True

    async def list_users(self, skip: int = 0, limit: int = 100) -> list[User]:
        return await self.repo.list_users(skip, limit)

    async def count_users(self) -> int:
        return await self.repo.count()

    async def delete_user(self, user_id: UUID) -> bool:
        return await self.repo.delete(user_id)
