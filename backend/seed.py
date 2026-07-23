import asyncio
from app.database.session import AsyncSessionLocal
from app.models.user import User
from app.core.security import get_password_hash


async def seed():
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(select(User).where(User.email == "admin@iq-ai.com"))
        existing = result.scalar_one_or_none()
        if not existing:
            admin = User(
                email="admin@iq-ai.com",
                username="admin",
                full_name="Admin User",
                hashed_password=get_password_hash("admin123"),
                role="admin",
                is_active=True,
                is_verified=True,
            )
            session.add(admin)
            await session.commit()
            print("Admin user created: admin@iq-ai.com / admin123")
        else:
            print("Admin user already exists")


if __name__ == "__main__":
    asyncio.run(seed())
