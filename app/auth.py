from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.services.api_key_service import is_valid_key

security = HTTPBearer(auto_error=False)

async def verify_api_key(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> str:
    if not credentials or not credentials.credentials:
        raise HTTPException(401, detail="Missing Authorization: Bearer <api_key>")

    if not await is_valid_key(db, credentials.credentials):
        raise HTTPException(403, detail="Invalid, expired, or revoked API key")
    return credentials.credentials