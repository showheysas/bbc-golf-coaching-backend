from sqlalchemy.ext.asyncio import AsyncSession
from app.models import get_db
from fastapi import Depends
import os
from dotenv import load_dotenv

load_dotenv()

async def get_database() -> AsyncSession:
    """Get database session dependency"""
    async for session in get_db():
        yield session

def get_default_user_id() -> str:
    """Get default user ID for development"""
    return os.getenv("DEFAULT_USER_ID", "550e8400-e29b-41d4-a716-446655440000")

def get_default_coach_id() -> str:
    """Get default coach ID for development"""
    return os.getenv("DEFAULT_COACH_ID", "6ba7b810-9dad-11d1-80b4-00c04fd430c8")