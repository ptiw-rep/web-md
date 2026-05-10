from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.db import get_db
from app.services.api_key_service import create_api_key, revoke_key, list_keys
from app.config import get_settings
import logging

router = APIRouter(prefix="/admin")
logger = logging.getLogger("admin")

class GenerateKeyRequest(BaseModel):
    admin_secret: str
    description: str = ""
    days_valid: int = 365

def verify_admin_secret(admin_secret: str):
    settings = get_settings()
    if admin_secret != settings.admin_secret:
        raise HTTPException(403, detail="Invalid admin secret")

@router.post("/keys/generate")
async def generate_key(req: GenerateKeyRequest, db: AsyncSession = Depends(get_db)):
    verify_admin_secret(req.admin_secret)
    new_key = await create_api_key(db, req.description, req.days_valid)
    return {"api_key": new_key, "message": "Key saved to SQLite. Store it securely."}

@router.get("/keys")
async def get_keys(admin_secret: str, db: AsyncSession = Depends(get_db)):
    verify_admin_secret(admin_secret)
    return await list_keys(db)

@router.delete("/keys/{key_id}")
async def delete_key(key_id: int, admin_secret: str, db: AsyncSession = Depends(get_db)):
    verify_admin_secret(admin_secret)
    success = await revoke_key(db, key_id)
    if not success:
        raise HTTPException(404, detail="Key not found")
    return {"message": f"Key {key_id} revoked successfully"}