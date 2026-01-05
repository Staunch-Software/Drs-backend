# app/api/deps.py
import uuid
from typing import Optional
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.user import User
from app.models.enums import UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/login/access-token", auto_error=False)

async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme), 
    db: AsyncSession = Depends(get_db)
) -> User:
    # FOR TESTING: Always return the user we inserted in Step 1
    return User(
        id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
        email="test@maritime.com",
        full_name="Test Chief",
        role=UserRole.CHIEF_ENGINEER,
        is_active=True
    )