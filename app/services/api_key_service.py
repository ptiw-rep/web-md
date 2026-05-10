from datetime import datetime, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.api_key import APIKey
import secrets

async def create_api_key(db: AsyncSession, description: str = "", days_valid: int = 365) -> str:
    new_key = f"mdexp_{secrets.token_urlsafe(32)}"
    expires_at = datetime.utcnow() + timedelta(days=days_valid) if days_valid > 0 else None
    db_key = APIKey(key=new_key, description=description, expires_at=expires_at)
    db.add(db_key)
    await db.commit()
    await db.refresh(db_key)
    return new_key

async def is_valid_key(db: AsyncSession, key: str) -> bool:
    result = await db.execute(select(APIKey).where(APIKey.key == key, APIKey.is_active == True))
    db_key = result.scalar_one_or_none()
    if not db_key:
        return False
    if db_key.expires_at and datetime.utcnow() > db_key.expires_at:
        return False
    return True

async def revoke_key(db: AsyncSession, key_id: int) -> bool:
    result = await db.execute(select(APIKey).where(APIKey.id == key_id))
    db_key = result.scalar_one_or_none()
    if not db_key:
        return False
    db_key.is_active = False
    await db.commit()
    return True

async def list_keys(db: AsyncSession) -> list[dict]:
    result = await db.execute(select(APIKey).order_by(APIKey.created_at.desc()))
    keys = result.scalars().all()
    return [
        {
            "id": k.id, "key_preview": f"{k.key[:8]}...", "description": k.description,
            "is_active": k.is_active, "created_at": k.created_at.isoformat() if k.created_at else None,
            "expires_at": k.expires_at.isoformat() if k.expires_at else None
        }
        for k in keys
    ]