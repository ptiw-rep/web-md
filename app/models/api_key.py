from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean, func
from app.models.base import Base  # ✅ Import from new location

class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(64), unique=True, nullable=False, index=True)
    description = Column(String(255), default="")
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, server_default=func.now())
    expires_at = Column(DateTime, nullable=True)