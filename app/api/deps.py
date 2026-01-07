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
        print(f"DEBUG: Received Token: {token[:10]}...")
        # 1. Decode the Token
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
        
        # 2. Extract User ID ("sub" holds the ID)
        token_data = payload.get("sub")
        print(f"DEBUG: Decoded Token Data (sub): {token_data}")

        if token_data is None:
            print("DEBUG: Token is valid but 'sub' field is missing!")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Could not validate credentials",
            )

    except (JWTError, ValidationError) as e:
        print(f"DEBUG: JWT Decode Error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )

    # 3. Fetch User from DB (Include Vessels Relationship)
    stmt = select(User).where(User.id == token_data).options(selectinload(User.vessels))
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        print(f"DEBUG: User ID {token_data} not found in database!")
        raise HTTPException(status_code=404, detail="User not found")
    
    if not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    # 4. Return the Real Database User Object
    print(f"DEBUG: Successfully authenticated user: {user.email}")
    return user