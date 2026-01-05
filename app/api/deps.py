# app/api/deps.py
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models.user import User
from app.models.enums import UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/login/access-token")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    PHASE 1 TESTING AUTH
    """
    # 1. Try to get the first user from the DB
    result = await db.execute(select(User).limit(1))
    user = result.scalars().first()
    
    if not user:
        # 2. If DB is empty, return a mock Vessel User so testing works
        # IMPORTANT: assigned_vessel_imo must match a real IMO in your 'vessels' table
        return User(
            id="00000000-0000-0000-0000-000000000000",
            email="chief@vessel.com",
            full_name="Mock Chief Engineer",
            role=UserRole.CHIEF_ENGINEER,
            assigned_vessel_imo="9832913" # <--- MAKE SURE THIS IMO EXISTS IN YOUR DB
        )
        
    return user