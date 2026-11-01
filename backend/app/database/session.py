from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings
from app.database.url import normalize_database_url

connect_args = {}
database_url = normalize_database_url(settings.DATABASE_URL)
if "sqlite" in database_url:
    connect_args = {"check_same_thread": False}

async_engine = create_async_engine(
    database_url,
    echo=settings.DATABASE_ECHO,
    connect_args=connect_args,
    **({"pool_size": settings.DATABASE_POOL_SIZE, "max_overflow": settings.DATABASE_MAX_OVERFLOW} if "sqlite" not in database_url else {}),
)

AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
