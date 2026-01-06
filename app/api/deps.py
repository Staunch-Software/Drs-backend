from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User

# This tells FastAPI where the client gets the token (for Swagger UI)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"/api/v1/login/access-token")

async def get_current_user(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    """
    Validates the JWT Token and retrieves the User from the Database.
    """
    try:
        # 1. Decode the Token
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        # 2. Extract User ID ("sub" holds the ID)
        token_data = payload.get("sub")
        
        if token_data is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate credentials",
            )
            
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )

    # 3. Fetch User from DB (Include Vessels Relationship)
    stmt = select(User).where(User.id == token_data).options(selectinload(User.vessels))
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    # 4. Return the Real Database User Object
    return user