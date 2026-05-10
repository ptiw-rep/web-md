from pathlib import Path
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.config import get_settings
from app.models.base import Base

settings = get_settings()

# ✅ Ensure data directory exists
DATA_DIR = Path("./data")
DATA_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_URL = f"sqlite+aiosqlite:///{DATA_DIR}/api_keys.db"

engine = create_async_engine(
    DATABASE_URL,
    echo=settings.environment == "development",
    connect_args={"check_same_thread": False},
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

from app.models.api_key import APIKey  # noqa: E402, F401

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("PRAGMA journal_mode=WAL;"))

async def get_db():
    async with async_session() as session:
        yield session