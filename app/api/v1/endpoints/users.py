from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.core.database import get_db
from app.models.user import User
from app.models.vessel import Vessel
from app.schemas.user import UserCreate, UserResponse
from app.core.security import get_password_hash

router = APIRouter()

@router.post("/", response_model=UserResponse)
async def create_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    # 1. Check if Email already exists
    result = await db.execute(select(User).where(User.email == user_in.email))
    if result.scalars().first():
        raise HTTPException(
            status_code=400, 
            detail="The user with this email already exists."
        )

    # 2. Fetch the Vessel objects
    vessels_to_assign = []
    if user_in.assigned_vessel_imos:
        # FIX: Use Vessel.imo, not Vessel.imo_number
        stmt = select(Vessel).where(Vessel.imo.in_(user_in.assigned_vessel_imos))
        result = await db.execute(stmt)
        vessels_to_assign = result.scalars().all()

        # Validation: Did we find all ships?
        if len(vessels_to_assign) != len(user_in.assigned_vessel_imos):
            print("⚠️ Warning: Some IMO numbers provided do not exist in DB.")

    # 3. Create User
    new_user = User(
        email=user_in.email,
        password_hash=get_password_hash(user_in.password), # <--- CRITICAL FIX: 'password_hash'
        full_name=user_in.full_name,
        role=user_in.role,
        vessels=vessels_to_assign 
    )

    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Manually map response to avoid Pydantic validation errors on relationships
    return {
        "id": new_user.id,
        "email": new_user.email,
        "full_name": new_user.full_name,
        "role": new_user.role,
        "is_active": new_user.is_active,
        # Helper to return list of IMOs
        "assigned_vessel_imos": [v.imo for v in new_user.vessels]
    }