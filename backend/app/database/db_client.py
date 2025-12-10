
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings
from app.database.models import Base

# Create async engine
print(f"🔗 Database Engine URL: {settings.database_url.replace(settings.db_password, '***') if settings.db_password else settings.database_url}")
engine = create_async_engine(
    settings.database_url,
    echo=True,  # Set to True for SQL query logging - will show which database we're connecting to
    future=True
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # Commit if no exception occurred
            await session.commit()
        except Exception:
            # Rollback on exception
            await session.rollback()
            raise
        finally:
            await session.close()

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def close_db():
    await engine.dispose()
