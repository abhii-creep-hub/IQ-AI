import asyncio
import os
from app.database.session import AsyncSessionLocal
from app.models.user import User
from app.core.security import get_password_hash


async def seed():
    email = os.getenv("IQAI_ADMIN_EMAIL")
    username = os.getenv("IQAI_ADMIN_USERNAME")
    password = os.getenv("IQAI_ADMIN_PASSWORD")
    if not email or not username or not password:
        raise SystemExit("Set IQAI_ADMIN_EMAIL, IQAI_ADMIN_USERNAME, and IQAI_ADMIN_PASSWORD before seeding an admin account.")
    if len(password) < 12:
        raise SystemExit("IQAI_ADMIN_PASSWORD must contain at least 12 characters.")
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.email == email))
        existing = result.scalar_one_or_none()
        if not existing:
            admin = User(
                email=email,
                username=username,
                full_name="Admin User",
                hashed_password=get_password_hash(password),
                role="admin",
                is_active=True,
                is_verified=True,
            )
            session.add(admin)
            await session.commit()
            print(f"Admin user created: {email}")
        else:
            print("Admin user already exists")


if __name__ == "__main__":
    asyncio.run(seed())
