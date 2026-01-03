from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models.user import User
from app.models.enums import UserRole

# This tells FastAPI that the token comes from the login endpoint
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/login/access-token")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    TEMPORARY MOCK AUTHENTICATION
    In a real app, this decodes the JWT token.
    For now, we fetch the FIRST user in the DB to let you test.
    """
    
    # In a real app, we would decode the 'token' here.
    # For now, we ignore the token and just return a mock user or the first DB user.
    
    result = await db.execute(select(User).limit(1))
    user = result.scalars().first()
    
    if not user:
        # If DB is empty, create a fake in-memory user so code doesn't crash during testing
        return User(
            id="00000000-0000-0000-0000-000000000000",
            email="temp@admin.com",
            full_name="Temporary Admin",
            role=UserRole.SUPERINTENDENT,
            assigned_vessel_imo=None # Shore user (None)
        )
        
    return user